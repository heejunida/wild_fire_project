import pandas as pd
import numpy as np
import joblib
import json
import sys
import os

# --- Constants ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_NAME = 'area_log_final'

# --- Sigmoid Growth Curve Function ---
def sigmoid_growth(final_area, total_duration=12, k=0.5, t0=6):
    """
    Calculates the fire area at different time steps using a sigmoid function.
    """
    growth_predictions = {}
    for t in range(total_duration + 1):
        growth_factor = 1 / (1 + np.exp(-k * (t - t0)))
        end_factor = 1 / (1 + np.exp(-k * (total_duration - t0)))
        scaled_growth_factor = growth_factor / end_factor
        current_area = final_area * scaled_growth_factor
        growth_predictions[t] = round(current_area, 2) # Round for cleaner JSON
        
    return growth_predictions

# --- Main Prediction Function ---
def predict_growth_from_json(json_input):
    """
    Loads the trained model and predicts fire growth from a JSON input.
    """
    # --- Load Artifacts ---
    try:
        model_path = os.path.join(BASE_DIR, f'{MODEL_NAME}_model.joblib')
        imputer_path = os.path.join(BASE_DIR, f'{MODEL_NAME}_imputer.joblib')
        scaler_path = os.path.join(BASE_DIR, f'{MODEL_NAME}_scaler.joblib')
        columns_path = os.path.join(BASE_DIR, f'{MODEL_NAME}_columns.json')

        model = joblib.load(model_path)
        imputer = joblib.load(imputer_path)
        scaler = joblib.load(scaler_path)
        with open(columns_path, 'r') as f:
            model_columns = json.load(f)
    except FileNotFoundError as e:
        return json.dumps({"status": "error", "message": f"Could not find a required model file: {e}"})

    # --- Load and Prepare Input Data ---
    try:
        # Create a DataFrame from the input JSON
        input_df = pd.DataFrame([json_input])
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error creating DataFrame from JSON: {e}"})

    # Align columns with the model's training columns
    input_df_aligned = input_df.reindex(columns=model_columns, fill_value=0)
    
    # --- Preprocess and Predict ---
    input_imputed = imputer.transform(input_df_aligned)
    input_scaled = scaler.transform(input_imputed)
    
    predicted_log_area = model.predict(input_scaled)
    predicted_final_area = np.expm1(predicted_log_area)[0]

    # --- Calculate Growth Curve ---
    growth_curve = sigmoid_growth(predicted_final_area)
    
    # --- Format Output as JSON ---
    output_json = {
        "status": "success",
        "predicted_final_area_ha": round(predicted_final_area, 2),
        "growth_curve": {
            "3hr_ha": growth_curve.get(3),
            "6hr_ha": growth_curve.get(6),
            "9hr_ha": growth_curve.get(9),
            "12hr_ha": growth_curve.get(12)
        }
    }
    
    return json.dumps(output_json, indent=4)

if __name__ == '__main__':
    # Read the JSON string from standard input
    try:
        input_json_string = sys.stdin.read()
        input_data = json.loads(input_json_string)
        
        # Get the prediction
        result_json = predict_growth_from_json(input_data)
        
        # Print the final JSON result to standard output
        print(result_json)
        
    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "Invalid JSON format received."}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"An unexpected error occurred: {e}"}))