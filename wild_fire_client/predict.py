import pandas as pd
import numpy as np
import joblib
import json
import sys
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')
warnings.filterwarnings('ignore', category=FutureWarning)

def load_models_and_metadata(base_path):
    """Loads all the trained models and their metadata files."""
    try:
        models = {
            'area_model': joblib.load(base_path + 'area_regressor_model.joblib'),
            'speed_model': joblib.load(base_path + 'speed_classifier_model.joblib'),
            'scaler': joblib.load(base_path + 'speed_model_scaler.joblib')
        }
        with open(base_path + 'area_model_columns.json', 'r') as f:
            models['area_cols'] = json.load(f)
        with open(base_path + 'speed_model_columns.json', 'r') as f:
            models['speed_cols'] = json.load(f)
        with open(base_path + 'speed_model_skewed_features.json', 'r') as f:
            models['skewed_cols'] = json.load(f)
        return models
    except FileNotFoundError as e:
        print(json.dumps({"error": f"A required model file was not found: {e}. Please run the main training script."}))
        sys.exit(1)

def prepare_features_for_prediction(features_json, models):
    """
    Prepares the full feature-engineered JSON for prediction by selecting only
    the columns that the models were trained on.
    """
    df = pd.DataFrame([features_json])

    # --- Data Cleaning Step (similar to clean_and_prepare_data in training) ---
    # Select only the columns that the area model was trained on.
    # This is the crucial step that removes all the unnecessary features.
    area_features = df[models['area_cols']].copy()
    
    # Select only the columns that the speed model was trained on.
    speed_features = df[models['speed_cols']].copy()

    # Convert all feature columns to numeric, coercing errors
    for col in area_features.columns:
        area_features[col] = pd.to_numeric(area_features[col], errors='coerce')
    area_features = area_features.fillna(0)
    
    for col in speed_features.columns:
        speed_features[col] = pd.to_numeric(speed_features[col], errors='coerce')
    speed_features = speed_features.fillna(0)

    # --- Transformations for Speed Model ---
    for col in models['skewed_cols']:
        if col in speed_features.columns:
            speed_features[col] = np.sign(speed_features[col]) * np.log1p(np.abs(speed_features[col]))
    
    scaled_speed_features = models['scaler'].transform(speed_features)
    scaled_speed_df = pd.DataFrame(scaled_speed_features, columns=models['speed_cols'])

    return area_features, scaled_speed_df

def main(input_json_string):
    """Main prediction pipeline."""
    try:
        features_dict = json.loads(input_json_string)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON received from the pre-processing scripts."}))
        sys.exit(1)

    model_path = '/Users/heejunida/wild_fire_project/'
    models = load_models_and_metadata(model_path)

    area_features, speed_features_scaled = prepare_features_for_prediction(features_dict, models)

    # Make predictions
    predicted_area_log = models['area_model'].predict(area_features)
    predicted_area_ha = np.expm1(predicted_area_log)[0]
    predicted_speed_category = models['speed_model'].predict(speed_features_scaled)[0]

    # --- NEW: Calculate predicted distance (radius) in meters ---
    # This assumes the fire spread is roughly circular. 1 hectare = 10,000 m^2.
    # Area = pi * r^2  =>  r = sqrt(Area / pi)
    predicted_distance_m = np.sqrt(predicted_area_ha * 10000 / np.pi)

    # Create the final JSON output
    output = {
        "predicted_area_ha": float(predicted_area_ha),
        "predicted_speed_category": int(predicted_speed_category),
        "wind_direction_deg": float(features_dict.get('WD10M_0h', -999.0)), # Use a clear placeholder
        "predicted_distance_m": float(predicted_distance_m)
    }
    
    print(json.dumps(output))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main(sys.stdin.read())
