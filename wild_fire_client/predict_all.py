import pandas as pd
import numpy as np
import joblib
import json
import sys
import os

# --- Constants ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS = {
    'area_low': 'area_quantile_low',
    'area_median': 'area_quantile_median',
    'area_high': 'area_quantile_high',
    'fwi': 'fwi',
    'direction': 'direction',
    'distance': 'distance'
}
# --- NEW: Add a sanity cap for FWI predictions ---
FWI_REALISTIC_MAX = 150.0

def load_artifacts(model_name_key):
    """Loads model and preprocessing artifacts for a given model key."""
    model_file_name = MODELS[model_name_key]
    try:
        if 'area' in model_name_key:
            artifact_name = 'area_quantile_median'
        else:
            artifact_name = model_file_name

        model_path = os.path.join(BASE_DIR, f'{model_file_name}_model.joblib')
        imputer_path = os.path.join(BASE_DIR, f'{artifact_name}_imputer.joblib')
        scaler_path = os.path.join(BASE_DIR, f'{artifact_name}_scaler.joblib')
        columns_path = os.path.join(BASE_DIR, f'{artifact_name}_columns.json')

        model = joblib.load(model_path)
        imputer = joblib.load(imputer_path)
        scaler = joblib.load(scaler_path)
        with open(columns_path, 'r') as f:
            columns = json.load(f)
        
        return model, imputer, scaler, columns
    except FileNotFoundError as e:
        raise Exception(f"Could not find a required model file for '{model_name_key}': {e}")

def predict_all(input_data):
    """
    Loads all trained models and returns a comprehensive prediction JSON.
    """
    predictions = {}
    input_df = pd.DataFrame([input_data])

    for model_key in MODELS.keys():
        model, imputer, scaler, model_columns = load_artifacts(model_key)
        
        input_aligned = input_df.reindex(columns=model_columns, fill_value=0)
        input_imputed = imputer.transform(input_aligned)
        input_scaled = scaler.transform(input_imputed)
        
        prediction = model.predict(input_scaled)[0]
        
        if 'area' in model_key:
            area_val = np.expm1(prediction)
            predictions[model_key.replace('_', '_pred_')] = float(round(area_val, 4))
        elif model_key == 'fwi':
            fwi_val = float(round(prediction, 4))
            # --- FIX: Apply the sanity cap to the FWI prediction ---
            predictions['fwi_pred'] = min(fwi_val, FWI_REALISTIC_MAX)
        elif model_key == 'direction':
            predictions['dir_pred'] = int(prediction)
        elif model_key == 'distance':
            predictions['distance_pred'] = float(round(prediction, 4))

    if predictions.get('area_pred_low', 0) > predictions.get('area_pred_median', 0):
        predictions['area_pred_low'] = predictions['area_pred_median']
    if predictions.get('area_pred_median', 0) > predictions.get('area_pred_high', 0):
        predictions['area_pred_high'] = predictions['area_pred_median']

    return {"status": "success", **predictions}

if __name__ == '__main__':
    try:
        input_json_string = sys.stdin.read()
        input_data = json.loads(input_json_string)
        result_json = predict_all(input_data)
        print(json.dumps(result_json, indent=4))
    except Exception as e:
        # Print the full error to stderr for logging, and a clean JSON to stdout for the Java app
        print(f"Error in predict_all.py: {e}", file=sys.stderr)
        print(json.dumps({"status": "error", "message": f"An unexpected error occurred in Python: {e}"}))