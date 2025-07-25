import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, f1_score
import xgboost as xgb
import argparse
import warnings
import joblib
import json
import os
from sklearn.preprocessing import RobustScaler

warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')
warnings.filterwarnings('ignore', category=FutureWarning)

def clean_and_prepare_data(df, target_col='fire_area'):
    """
    Prepares the enriched dataframe for a specific modeling target.
    """
    print(f"Preparing data for target '{target_col}'.")
    
    analysis_cols = ['start_latitude', 'start_longitude', 'WD10M_0h']
    object_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    cols_to_drop = sorted(list(set(
        object_cols + 
        analysis_cols +
        [target_col, 'fire_area', 'fire_area_log', 'spread_rate']
    )))
    
    X = df.drop(columns=cols_to_drop, errors='ignore')
    y = df[target_col]

    if 'land_cover_name' in X.columns:
        X = pd.get_dummies(X, columns=['land_cover_name'], prefix='land_cover')
    
    print(f"Prepared dataset. Features shape: {X.shape}")
    return X, y

def train_area_regressor(df):
    """
    Trains an XGBoost model to predict the final fire area.
    """
    print("\n--- Part 1: Predicting Fire Area ---")
    df['fire_area_log'] = np.log1p(df['fire_area'])

    print("\nDEBUG: Columns in `df` before clean_and_prepare_data:")
    print(list(df.columns))

    X, y = clean_and_prepare_data(df, target_col='fire_area_log')
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # --- FIX: Impute missing values after splitting to prevent data leakage ---
    imputation_values = X_train.median()
    X_train = X_train.fillna(imputation_values)
    X_test = X_test.fillna(imputation_values)

    print("Training XGBoost Regressor for Area...")
    model = xgb.XGBRegressor(
        colsample_bytree=0.8, learning_rate=0.1, max_depth=7, 
        n_estimators=200, subsample=1.0, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)

    joblib.dump(model, 'area_regressor_model.joblib')
    print("\n✅ Area regressor model saved.")
    
    with open('area_model_columns.json', 'w') as f:
        json.dump(list(X_train.columns), f)
    print("✅ Area model columns saved.")

    y_pred_log = model.predict(X_test)
    y_pred_actual = np.expm1(y_pred_log)
    y_test_actual = np.expm1(y_test)

    mae = mean_absolute_error(y_test_actual, y_pred_actual)
    r2 = r2_score(y_test_actual, y_pred_actual)
    
    print(f"\nArea Model Evaluation: MAE: {mae:.3f}, R² Score: {r2:.3f}")

    # --- NEW: Advanced Performance Evaluation by Fire Size Quantile ---
    print("\n--- Performance Evaluation by Fire Size Quantile ---")
    results_df = pd.DataFrame({'Actual_Area': y_test_actual, 'Predicted_Area': y_pred_actual})
    
    results_df['quantile_group'] = pd.qcut(
        results_df['Actual_Area'], 
        q=[0, 0.25, 0.5, 0.75, 1.0], 
        labels=['Q1 (Smallest 25%)', 'Q2 (25-50%)', 'Q3 (50-75%)', 'Q4 (Largest 25%)'],
        duplicates='drop'
    )
    
    quantile_mae = results_df.groupby('quantile_group', observed=False).apply(
        lambda g: mean_absolute_error(g['Actual_Area'], g['Predicted_Area'])
    )
    
    print("Mean Absolute Error (MAE) for each fire size group:")
    for group, mae_val in quantile_mae.items():
        group_range = results_df[results_df['quantile_group'] == group]['Actual_Area'].agg(['min', 'max'])
        print(f"  - {group} (Range: {group_range['min']:.2f}-{group_range['max']:.2f} ha): MAE = {mae_val:.3f} ha")

    print("\nThis provides a much clearer view of the model's performance on small vs. large fires.")
    # --- End New Evaluation ---

    return model, X_train.columns

def train_fwi_regressor(df):
    """
    Trains an XGBoost model to predict the FWI at ignition, using RobustScaler.
    """
    print("\n--- Part 2: Predicting Fire Weather Index (FWI) for Speed ---")
    
    df_fwi = df.dropna(subset=['FWI_0h']).copy()

    X, y = clean_and_prepare_data(df_fwi, target_col='FWI_0h')
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # --- FIX: Impute missing values after splitting ---
    imputation_values = X_train.median()
    X_train = X_train.fillna(imputation_values)
    X_test = X_test.fillna(imputation_values)

    scaler = RobustScaler()
    y_train_scaled = scaler.fit_transform(y_train.values.reshape(-1, 1)).ravel()

    print("Training XGBoost Regressor for FWI with RobustScaler...")
    model = xgb.XGBRegressor(
        colsample_bytree=0.8, learning_rate=0.1, max_depth=5, 
        n_estimators=150, subsample=1.0, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train_scaled)

    joblib.dump(model, 'fwi_regressor_model.joblib')
    joblib.dump(scaler, 'fwi_scaler.joblib')
    print("\n✅ FWI regressor model and scaler saved.")
    
    with open('fwi_model_columns.json', 'w') as f:
        json.dump(list(X_train.columns), f)
    print("✅ FWI model columns saved.")

    y_pred_scaled = model.predict(X_test)
    y_pred_unscaled = scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()

    mae = mean_absolute_error(y_test, y_pred_unscaled)
    r2 = r2_score(y_test, y_pred_unscaled)
    
    print(f"\nFWI Model Evaluation: MAE: {mae:.3f}, R² Score: {r2:.3f}")

def train_direction_classifier(df):
    """
    Trains an XGBoost model to classify the primary direction of fire spread.
    """
    print("\n--- Part 3: Classifying Fire Spread Direction ---")
    df_dir = df.dropna(subset=['WD10M_0h']).copy()
    
    df_dir['direction_category'] = df_dir['WD10M_0h'].apply(lambda d: int(round(d / 45.)) % 8)

    X, y = clean_and_prepare_data(df_dir, target_col='direction_category')
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # --- FIX: Impute missing values after splitting ---
    imputation_values = X_train.median()
    X_train = X_train.fillna(imputation_values)
    X_test = X_test.fillna(imputation_values)

    print("Training XGBoost Classifier for Direction...")
    model = xgb.XGBClassifier(
        objective='multi:softmax', num_class=8, eval_metric='mlogloss', 
        n_estimators=150, learning_rate=0.1, max_depth=5, 
        random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)

    joblib.dump(model, 'direction_classifier_model.joblib')
    print("\n✅ Direction classifier model saved.")
    
    with open('direction_model_columns.json', 'w') as f:
        json.dump(list(X_train.columns), f)
    print("✅ Direction model columns saved.")

    y_pred = model.predict(X_test)
    f1 = f1_score(y_test, y_pred, average='weighted')
    print(f"\nDirection Model Evaluation: Weighted F1-Score: {f1:.3f}")

def main(file_path):
    """Main function to run the entire pipeline."""
    try:
        df = pd.read_csv(file_path, encoding="utf-8")
        
        area_model, area_cols = train_area_regressor(df.copy())
        train_fwi_regressor(df.copy())
        train_direction_classifier(df.copy())
        
        # --- Plot Top 20 Feature Importances for the Area Model ---
        importances = area_model.feature_importances_
        top_indices = np.argsort(importances)[-20:]
        
        plt.figure(figsize=(10, 8))
        plt.title('Top 20 Feature Importances (Area Model)')
        plt.barh(range(len(top_indices)), importances[top_indices], color='c', align='center')
        plt.yticks(range(len(top_indices)), [area_cols[i] for i in top_indices])
        plt.xlabel('Feature Importance')
        plt.tight_layout()
        plt.savefig('area_model_feature_importance.png')
        print("\n✅ Saved area model feature importance plot.")

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Wildfire ML Pipeline")
    parser.add_argument(
        '--file', 
        type=str, 
        default="enriched_training_data.csv",
        help="Path to the enriched training data CSV file."
    )
    args = parser.parse_args()
    # --- FIX: Construct the absolute path to the file ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, args.file)
    main(file_path)
