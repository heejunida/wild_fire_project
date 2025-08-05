import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error, r2_score, f1_score, confusion_matrix
import xgboost as xgb
import argparse
import warnings
import joblib
import json
import os
from sklearn.preprocessing import RobustScaler
from sklearn.impute import SimpleImputer

warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')
warnings.filterwarnings('ignore', category=FutureWarning)

# --- Constants ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILE = "cleaned_ignition_data.csv"
TARGET_AREA = 'fire_area'
TARGET_FWI = 'FWI_0h'
TARGET_DIRECTION = 'direction_category'
TARGET_DISTANCE = 'effective_distance'
TOP_N_FEATURES = 40

# --- Utility Functions ---
def prepare_data(df, target_col, feature_columns=None):
    """Prepares the dataframe for a specific modeling target."""
    y = df[target_col]
    if feature_columns:
        X = df[feature_columns]
    else:
        analysis_cols = ['start_latitude', 'start_longitude', 'WD10M_0h']
        object_cols = df.select_dtypes(include=['object']).columns.tolist()
        base_drop = ['fire_area', 'fire_area_log', 'effective_distance', 'spread_rate', 'direction_category', 'FWI_0h']
        cols_to_drop = sorted(list(set(object_cols + analysis_cols + base_drop)))
        X = df.drop(columns=cols_to_drop, errors='ignore')
    if 'land_cover_name' in X.columns:
        X = pd.get_dummies(X, columns=['land_cover_name'], prefix='land_cover')
    return X, y

def plot_confusion_matrix(y_true, y_pred, model_name):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8)); sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=range(8), yticklabels=range(8))
    plt.title(f'Confusion Matrix for {model_name}'); plt.xlabel('Predicted Direction'); plt.ylabel('Actual Direction')
    plt.savefig(os.path.join(BASE_DIR, f'{model_name}_confusion_matrix.png')); plt.close()

def plot_feature_importance(model, columns, model_name):
    importances = model.feature_importances_
    top_indices = np.argsort(importances)[-20:]
    plt.figure(figsize=(10, 8)); plt.title(f'Top 20 Feature Importances ({model_name})')
    plt.barh(range(len(top_indices)), importances[top_indices], color='c', align='center')
    plt.yticks(range(len(top_indices)), [columns[i] for i in top_indices])
    plt.xlabel('Feature Importance'); plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, f'{model_name}_feature_importance.png')); plt.close()

# --- Model Training Function ---
def train_model(X, y, model_name, model_class, param_grid, is_classifier=False):
    """A generic function to train a model with GridSearchCV."""
    print(f"\n--- Training {model_name} ---")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    imputer = SimpleImputer(strategy='median')
    X_train_imputed = imputer.fit_transform(X_train)
    X_test_imputed = imputer.transform(X_test)
    
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train_imputed)
    X_test_scaled = scaler.transform(X_test_imputed)

    grid_search = GridSearchCV(estimator=model_class, param_grid=param_grid, scoring='neg_mean_absolute_error' if not is_classifier else 'f1_weighted', cv=3, n_jobs=-1, verbose=1)
    grid_search.fit(X_train_scaled, y_train)
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # --- Evaluate and Print Metrics ---
    y_pred = best_model.predict(X_test_scaled)
    metrics = {}
    print(f"\n--- Results for {model_name} ---")
    print(f"  Best Hyperparameters: {best_params}")
    if is_classifier:
        f1 = f1_score(y_test, y_pred, average='weighted')
        metrics = {'f1_weighted': f1}
        print(f"  Weighted F1-Score: {f1:.4f}")
        plot_confusion_matrix(y_test, y_pred, model_name)
        print(f"  Confusion Matrix saved to {model_name}_confusion_matrix.png")
    else:
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        metrics = {'mae': mae, 'r2': r2}
        print(f"  Mean Absolute Error (MAE): {mae:.4f}")
        print(f"  R-squared (R²): {r2:.4f}")
    print("-" * (23 + len(model_name)))

    joblib.dump(best_model, os.path.join(BASE_DIR, f'{model_name}_model.joblib'))
    joblib.dump(scaler, os.path.join(BASE_DIR, f'{model_name}_scaler.joblib'))
    joblib.dump(imputer, os.path.join(BASE_DIR, f'{model_name}_imputer.joblib'))
    with open(os.path.join(BASE_DIR, f'{model_name}_columns.json'), 'w') as f:
        json.dump(list(X.columns), f)
    print(f"✅ {model_name} artifacts saved.")
    
    plot_feature_importance(best_model, X.columns, model_name)
    return best_model, X.columns, metrics, best_params

# --- Main Execution ---
def main(file_path):
    try:
        df = pd.read_csv(file_path, encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found."); return

    regressor_params = {'n_estimators': [100, 200], 'learning_rate': [0.05, 0.1], 'max_depth': [5, 7]}
    classifier_params = {'n_estimators': [100, 200], 'learning_rate': [0.05, 0.1], 'max_depth': [5, 7], 'objective': ['multi:softmax'], 'num_class': [8], 'eval_metric': ['mlogloss']}

    all_metrics = []
    all_params = []

    # --- 1. Area Model (Feature Selection Pass) ---
    print("\n" + "="*50 + "\nSTEP 1: AREA MODEL FEATURE SELECTION\n" + "="*50)
    df['fire_area_log'] = np.log1p(df[TARGET_AREA])
    X_full, y_area = prepare_data(df, 'fire_area_log')
    _, _, metrics, params = train_model(X_full, y_area, 'area_log_initial', xgb.XGBRegressor(random_state=42), regressor_params)
    all_metrics.append({'model_name': 'area_log_initial', **metrics})
    all_params.append({'model_name': 'area_log_initial', **params})
    
    # Re-load for feature importance on the full model
    initial_area_model = joblib.load(os.path.join(BASE_DIR, 'area_log_initial_model.joblib'))
    importances = initial_area_model.feature_importances_
    top_indices = np.argsort(importances)[-TOP_N_FEATURES:]
    top_features = [X_full.columns[i] for i in top_indices]
    print(f"\nIdentified Top {TOP_N_FEATURES} features for the final area models.")
    X_top, y_top = prepare_data(df, 'fire_area_log', feature_columns=top_features)

    # --- 2. Area Quantile Models (for Confidence Interval) ---
    print("\n" + "="*50 + "\nSTEP 2: AREA QUANTILE MODEL TRAINING\n" + "="*50)
    quantiles = {'low': 0.1, 'median': 0.5, 'high': 0.9}
    for name, alpha in quantiles.items():
        model_name = f'area_quantile_{name}'
        model = xgb.XGBRegressor(objective='reg:quantileerror', quantile_alpha=alpha, random_state=42)
        _, _, metrics, params = train_model(X_top, y_top, model_name, model, regressor_params)
        all_metrics.append({'model_name': model_name, **metrics})
        all_params.append({'model_name': model_name, **params})

    # --- 3. FWI, Direction, Distance Models ---
    print("\n" + "="*50 + "\nSTEP 3: FWI, DIRECTION, DISTANCE MODELS\n" + "="*50)
    df_fwi = df.dropna(subset=[TARGET_FWI]).copy()
    X_fwi, y_fwi = prepare_data(df_fwi, TARGET_FWI)
    _, _, metrics, params = train_model(X_fwi, y_fwi, 'fwi', xgb.XGBRegressor(random_state=42), regressor_params)
    all_metrics.append({'model_name': 'fwi', **metrics})
    all_params.append({'model_name': 'fwi', **params})

    df_dir = df.dropna(subset=['WD10M_0h']).copy()
    df_dir[TARGET_DIRECTION] = df_dir['WD10M_0h'].apply(lambda d: int(round(d / 45.)) % 8)
    X_dir, y_dir = prepare_data(df_dir, TARGET_DIRECTION)
    _, _, metrics, params = train_model(X_dir, y_dir, 'direction', xgb.XGBClassifier(random_state=42), classifier_params, is_classifier=True)
    all_metrics.append({'model_name': 'direction', **metrics})
    all_params.append({'model_name': 'direction', **params})

    df[TARGET_DISTANCE] = np.sqrt(df[TARGET_AREA])
    X_dist, y_dist = prepare_data(df, TARGET_DISTANCE)
    _, _, metrics, params = train_model(X_dist, y_dist, 'distance', xgb.XGBRegressor(random_state=42), regressor_params)
    all_metrics.append({'model_name': 'distance', **metrics})
    all_params.append({'model_name': 'distance', **params})

    # --- 4. Performance and Hyperparameter Summary ---
    print("\n" + "="*50 + "\nSTEP 4: MODEL PERFORMANCE & HYPERPARAMETER SUMMARY\n" + "="*50)
    df_metrics = pd.DataFrame(all_metrics).set_index('model_name')
    df_params = pd.DataFrame(all_params).set_index('model_name')
    
    print("\n--- Performance Summary ---")
    print(df_metrics.to_string(float_format="%.4f"))
    
    print("\n--- Best Hyperparameters ---")
    print(df_params.to_string())

    df_metrics.to_csv(os.path.join(BASE_DIR, "model_performance_summary.csv"))
    df_params.to_csv(os.path.join(BASE_DIR, "model_hyperparameter_summary.csv"))
    print("\nPerformance and hyperparameter summaries saved to CSV files.")

    # Visualize Regression Metrics
    df_regr = df_metrics[df_metrics['r2'].notna()].sort_values('r2', ascending=False)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))
    
    sns.barplot(x=df_regr.index, y=df_regr['r2'], ax=ax1, palette='viridis')
    ax1.set_title('Model Comparison: R-squared (R²)', fontsize=16)
    ax1.set_ylabel('R² Score')
    ax1.tick_params(axis='x', rotation=45)

    df_regr_mae = df_regr.sort_values('mae', ascending=False)
    sns.barplot(x=df_regr_mae.index, y=df_regr_mae['mae'], ax=ax2, palette='plasma')
    ax2.set_title('Model Comparison: Mean Absolute Error (MAE) - Log Scale', fontsize=16)
    ax2.set_ylabel('MAE Score (Log Scale)')
    ax2.set_yscale('log')
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "model_performance_comparison.png"))
    print("Performance comparison plot saved to model_performance_comparison.png")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Wildfire ML Pipeline with Quantile Regression")
    parser.add_argument('--file', type=str, default=DEFAULT_FILE, help=f"Path to the training data CSV file. Defaults to '{DEFAULT_FILE}'.")
    args = parser.parse_args()
    main(os.path.join(BASE_DIR, args.file))