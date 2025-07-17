# -*- coding: utf-8 -*-
"""
This script runs a two-stage wildfire growth simulation using the v3 models.
It uses a specialized model for small fires and a general model for larger fires,
incorporating a momentum feature (`previous_hour_area`) for more realistic growth.
"""
import pandas as pd
import numpy as np
import joblib
import os
import matplotlib.pyplot as plt

# --- Configuration ---
DATA_PATH = 'preprocess/csv/final_data_with_features_with_correct_duration_time.csv'
MODEL_DIR = 'model/ensemble_models'
SMALL_FIRE_MODEL_DIR = os.path.join(MODEL_DIR, 'small_fire')
MODEL_SWITCH_THRESHOLD_HA = 10
FORCE_SWITCH_HOURS = 24  # New: Force switch to general model after this many hours

# --- 1. Load All v3 Models and Data ---
print("Loading all v3 models and data...")
try:
    # General models (v3)
    rf_general = joblib.load(os.path.join(MODEL_DIR, 'randomforest_model_v3.joblib'))
    xgb_general = joblib.load(os.path.join(MODEL_DIR, 'xgboost_model_v3.joblib'))
    cat_general = joblib.load(os.path.join(MODEL_DIR, 'catboost_model_v3.joblib'))
    
    # Specialized small-fire models (v3)
    rf_small = joblib.load(os.path.join(SMALL_FIRE_MODEL_DIR, 'randomforest_small_model_v3.joblib'))
    xgb_small = joblib.load(os.path.join(SMALL_FIRE_MODEL_DIR, 'xgboost_small_model_v3.joblib'))
    cat_small = joblib.load(os.path.join(SMALL_FIRE_MODEL_DIR, 'catboost_small_model_v3.joblib'))
    
    df = pd.read_csv(DATA_PATH)
    print("Resources loaded successfully.")
except FileNotFoundError as e:
    print(f"Error: A required file was not found. {e}")
    print("Please ensure you have run the 'ensemble.py' script to train the v3 models.")
    exit()

# --- 2. Feature Engineering (for baseline data) ---
# Note: The simulation loop dynamically creates these features.
# This section is for ensuring the initial DataFrame has the necessary columns.
print("Engineering interaction features for the dataset...")
df['duration_x_ws10m'] = df['fire_duration_hours'] * df['WS10M_mean']
df['duration_x_rh2m'] = df['fire_duration_hours'] * df['RH2M_mean']
df['duration_x_t2m'] = df['fire_duration_hours'] * df['T2M_mean']
# The 'previous_hour_area' is calculated dynamically in the simulation.
df['previous_hour_area'] = 0 
print("Interaction features created.")

# --- 3. Define Feature Columns (must match v3 models) ---
feature_cols = [
    'T2M_mean', 'T2M_max', 'T2M_min', 'T2M_std',
    'RH2M_mean', 'RH2M_min', 'RH2M_std',
    'WS2M_mean', 'WS2M_max', 'WS2M_std',
    'WS10M_mean', 'WS10M_max', 'WS10M_std',
    'WD2M_mean', 'WD10M_mean',
    'PRECTOTCORR_sum', 'PRECTOTCORR_max',
    'PS_mean', 'PS_std',
    'ALLSKY_SFC_SW_DWN_mean', 'ALLSKY_SFC_SW_DWN_max',
    'T2M_start', 'T2M_end', 'RH2M_start', 'RH2M_end',
    'WS2M_start', 'WS2M_end', 'WS10M_start', 'WS10M_end',
    'WD2M_start', 'WD2M_end', 'WD10M_start', 'WD10M_end',
    'PRECTOTCORR_start', 'PRECTOTCORR_end',
    'PS_start', 'PS_end',
    'ALLSKY_SFC_SW_DWN_start', 'ALLSKY_SFC_SW_DWN_end',
    'start_year', 'start_month', 'start_day', 'start_hour',
    'end_year', 'end_month', 'end_day', 'end_hour',
    'fire_duration_hours', 'start_weekday', 'start_quarter',
    'ndvi_before', 'elevation', 'slope', 'aspect', 'treecover_pre_fire_5x5',
    'T2M_diff', 'RH2M_ratio', 'PRECTOTCORR_intensity',
    'treecover_density_effect', 'duration_WS10M',
    'is_holiday', 'fire_season', 'extreme_wind', 'extreme_temp',
    'duration_x_ws10m', 'duration_x_rh2m', 'duration_x_t2m',
    'previous_hour_area'  # Added momentum feature
]

def interpolate_weather(initial_conditions, hour, total_duration):
    if total_duration <= 1:
        return initial_conditions
    fraction = hour / total_duration
    interp_cond = initial_conditions.copy()
    weather_features = ['T2M', 'RH2M', 'WS2M', 'WS10M', 'WD2M', 'WD10M', 'PRECTOTCORR', 'PS', 'ALLSKY_SFC_SW_DWN']
    for feat in weather_features:
        start_val = interp_cond.get(f'{feat}_start', interp_cond.get(f'{feat}_mean'))
        end_val = interp_cond.get(f'{feat}_end', interp_cond.get(f'{feat}_mean'))
        interp_cond[f'{feat}_mean'] = start_val + (end_val - start_val) * fraction
    return interp_cond

def run_two_stage_simulation(case_index, full_df, feature_order):
    case_data = full_df.iloc[case_index]
    actual_duration = int(case_data['fire_duration_hours'])
    actual_final_area = case_data['fire_area']

    if actual_duration <= 0:
        return None, None

    print(f"\n--- Simulating Fire for Case Index: {case_index} ---")
    print(f"Actual Duration: {actual_duration} hours, Actual Final Area: {actual_final_area:.4f} ha")

    simulation_results = {}
    current_area = 0  # This now represents the area at the *end* of the previous hour
    use_small_model = True

    initial_conditions = case_data.drop(labels=['fire_area']).to_dict()

    for hour in range(1, actual_duration + 1):
        interp_conditions = interpolate_weather(initial_conditions, hour, actual_duration)
        
        current_input_df = pd.DataFrame([interp_conditions])
        current_input_df['fire_duration_hours'] = hour
        
        # Set the momentum feature: the area from the previous hour's prediction
        current_input_df['previous_hour_area'] = current_area
        
        # Dynamically calculate interaction features for the current hour
        current_input_df['duration_x_ws10m'] = hour * current_input_df['WS10M_mean']
        current_input_df['duration_x_rh2m'] = hour * current_input_df['RH2M_mean']
        current_input_df['duration_x_t2m'] = hour * current_input_df['T2M_mean']
        
        # Ensure all columns are in the correct order and pass the DataFrame directly
        X_sim = current_input_df[feature_order]

        if use_small_model:
            rf_pred, xgb_pred, cat_pred = rf_small.predict(X_sim), xgb_small.predict(X_sim), cat_small.predict(X_sim)
        else:
            rf_pred, xgb_pred, cat_pred = rf_general.predict(X_sim), xgb_general.predict(X_sim), cat_general.predict(X_sim)

        blend_pred_log = 0.3 * rf_pred + 0.3 * xgb_pred + 0.4 * cat_pred
        predicted_total_area = np.expm1(blend_pred_log)[0]
        
        # Update current_area for the next loop iteration and for logging
        current_area = predicted_total_area
        simulation_results[hour] = current_area
        
        model_type = "Small-Fire Model" if use_small_model else "General Model"
        print(f"Hour {hour:02d}: Predicted Area = {current_area:.4f} ha (using {model_type})")

        # Check for model switch
        if use_small_model:
            if current_area >= MODEL_SWITCH_THRESHOLD_HA:
                print(f"---> Threshold reached at hour {hour}. Switching to General Model.")
                use_small_model = False
            elif hour >= FORCE_SWITCH_HOURS:
                print(f"---> Time limit reached at hour {hour}. Forcing switch to General Model.")
                use_small_model = False
            
    print("Simulation complete.")
    return simulation_results, actual_final_area

def plot_simulation(results, actual_area, case_index):
    if not results:
        return
    hours, predicted_areas = list(results.keys()), list(results.values())
    
    plt.figure(figsize=(12, 7))
    plt.plot(hours, predicted_areas, 'o-', label='Simulated Growth')
    plt.axhline(y=actual_area, color='r', linestyle='--', label=f'Actual Final Area ({actual_area:.2f} ha)')
    plt.axhline(y=MODEL_SWITCH_THRESHOLD_HA, color='g', linestyle=':', label=f'Model Switch Threshold ({MODEL_SWITCH_THRESHOLD_HA} ha)')
    if len(hours) > FORCE_SWITCH_HOURS:
        plt.axvline(x=FORCE_SWITCH_HOURS, color='purple', linestyle='-.', label=f'Forced Switch Time ({FORCE_SWITCH_HOURS} hrs)')

    plt.xlabel("Hour")
    plt.ylabel("Predicted Fire Area (ha)")
    plt.title(f"Two-Stage Simulation vs. Actual - Case {case_index}")
    plt.legend()
    plt.grid(True, which="both", ls="--")
    plt.savefig(f'simulation_case_{case_index}_v3_forced.png')
    plt.close()
    print(f"\nSaved simulation plot to simulation_case_{case_index}_v3_forced.png")

# --- Main Execution ---
if __name__ == "__main__":
    # Find a large fire to test the model switching
    large_fire_case_index = df['fire_area'].idxmax()
    
    results, actual_area = run_two_stage_simulation(
        case_index=large_fire_case_index, 
        full_df=df, 
        feature_order=feature_cols
    )
    
    if results:
        plot_simulation(results, actual_area, large_fire_case_index)
