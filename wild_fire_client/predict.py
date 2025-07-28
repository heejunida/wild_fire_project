import pandas as pd
import numpy as np
import joblib
import json
import sys
import warnings
import os
import time
import datetime
from save_to_db import save_prediction_to_oracle

warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')
warnings.filterwarnings('ignore', category=FutureWarning)

def load_models_and_metadata(base_path):
    """Loads all the trained models and their metadata files."""
    try:
        models = {
            'area_model': joblib.load(os.path.join(base_path, 'area_regressor_model.joblib')),
            'fwi_model': joblib.load(os.path.join(base_path, 'fwi_regressor_model.joblib')),
            'fwi_scaler': joblib.load(os.path.join(base_path, 'fwi_scaler.joblib'))
        }
        with open(os.path.join(base_path, 'area_model_columns.json'), 'r') as f:
            models['area_cols'] = json.load(f)
        with open(os.path.join(base_path, 'fwi_model_columns.json'), 'r') as f:
            models['fwi_cols'] = json.load(f)
        return models
    except FileNotFoundError as e:
        print(json.dumps({"error": f"A required model file was not found: {e}. Please run the main training script."}))
        sys.exit(1)

def prepare_features_for_prediction(features_json, model_cols):
    """
    Prepares the feature-engineered JSON for a specific model.
    """
    df = pd.DataFrame([features_json])

    # Ensure all expected columns exist, filling missing ones with 0
    for col in model_cols:
        if col not in df.columns:
            df[col] = 0
    
    # Select and order columns as the model expects
    features = df[model_cols].copy()

    # Convert all feature columns to numeric, coercing errors
    for col in features.columns:
        features[col] = pd.to_numeric(features[col], errors='coerce')
    features = features.fillna(0)
    
    return features

def main(input_json_string):
    """Main prediction pipeline."""
    try:
        features_dict = json.loads(input_json_string)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON received from the pre-processing scripts."}))
        sys.exit(1)

    model_path = os.path.dirname(os.path.abspath(__file__))
    models = load_models_and_metadata(model_path)

    # Prepare features for each model separately
    area_features = prepare_features_for_prediction(features_dict, models['area_cols'])
    fwi_features = prepare_features_for_prediction(features_dict, models['fwi_cols'])

    # Make predictions
    predicted_area_log = models['area_model'].predict(area_features)
    predicted_area_ha = np.expm1(predicted_area_log)[0]
    
    predicted_fwi_scaled = models['fwi_model'].predict(fwi_features)
    predicted_fwi = models['fwi_scaler'].inverse_transform(predicted_fwi_scaled.reshape(-1, 1)).ravel()[0]

    predicted_distance_m = np.sqrt(predicted_area_ha * 10000 / np.pi)

    # --- NEW: Save the results to the Oracle database ---
    # We need an ID and a datetime for the database record.
    # The Java controller should pass the requestId and the full datetime string.
    fire_id = features_dict.get('requestId', f"pred-{int(time.time())}")
    fire_datetime_str = features_dict.get('fire_datetime', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # The direction model is separate, so we'll just use the raw wind direction for now.
    # A more advanced implementation would run the direction model here as well.
    wind_direction_deg = float(features_dict.get('WD10M_0h', -999.0))
    dir_pred = degrees_to_cardinal(wind_direction_deg) # Helper function needed

    save_prediction_to_oracle(
        fire_id=fire_id,
        fire_datetime=fire_datetime_str,
        lat=features_dict.get('lat'),
        lon=features_dict.get('lng'),
        area_pred=float(predicted_area_ha),
        fwi_pred=float(predicted_fwi),
        dir_pred=dir_pred,
        dist_pred=float(predicted_distance_m),
        features_json=features_dict
    )

    # Create the JSON output for the frontend
    output = {
        "predicted_area_ha": float(predicted_area_ha),
        "predicted_fwi": float(predicted_fwi),
        "wind_direction_deg": wind_direction_deg,
        "predicted_distance_m": float(predicted_distance_m)
    }
    
    print(json.dumps(output))

def degrees_to_cardinal(d):
    """Converts wind direction in degrees to 8-point cardinal directions."""
    if d <= -999.0:
        return "N/A"
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ix = int(round(d / 45.)) % 8
    return dirs[ix]

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main(sys.stdin.read())

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main(sys.stdin.read())
