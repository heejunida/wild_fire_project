# -*- coding: utf-8 -*-
"""
This script trains two sets of ensemble models:
1. General models trained on all data with interaction features.
2. Specialized models trained only on small fires (<10 ha).

Both sets are saved for use in the simulation script.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
import joblib
import os

# --- Configuration ---
DATA_PATH = 'preprocess/csv/final_data_with_features_with_correct_duration_time.csv'
MODEL_DIR = 'model/ensemble_models'
SMALL_FIRE_MODEL_DIR = os.path.join(MODEL_DIR, 'small_fire')
SMALL_FIRE_THRESHOLD_HA = 10  # Fires smaller than 10 hectares

# --- 1. Load Data and Engineer Features ---
print("Loading data and engineering features...")
try:
    df = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    print(f"Error: Dataset not found at '{DATA_PATH}'. Exiting.")
    exit()

df['duration_x_ws10m'] = df['fire_duration_hours'] * df['WS10M_mean']
df['duration_x_rh2m'] = df['fire_duration_hours'] * df['RH2M_mean']
df['duration_x_t2m'] = df['fire_duration_hours'] * df['T2M_mean']
print("Interaction features created.")

# --- 2. Define Feature Columns ---
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
    'duration_x_ws10m', 'duration_x_rh2m', 'duration_x_t2m'
]
target_col = 'fire_area'

# --- 3. Train and Save General Models (on all data) ---
print("\n--- Training General Models (v2) on Full Dataset ---")
X = df[feature_cols]
y = np.log1p(df[target_col])

rf_general = RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42, n_jobs=-1).fit(X, y)
xgb_general = XGBRegressor(n_estimators=200, learning_rate=0.1, random_state=42, n_jobs=-1).fit(X, y)
cat_general = CatBoostRegressor(iterations=200, learning_rate=0.1, random_state=42, verbose=0).fit(X, y)

os.makedirs(MODEL_DIR, exist_ok=True)
joblib.dump(rf_general, os.path.join(MODEL_DIR, 'randomforest_model_v2.joblib'))
joblib.dump(xgb_general, os.path.join(MODEL_DIR, 'xgboost_model_v2.joblib'))
joblib.dump(cat_general, os.path.join(MODEL_DIR, 'catboost_model_v2.joblib'))
print("General models (v2) trained and saved.")

# --- 4. Train and Save Specialized Models (on small fires) ---
print(f"\n--- Training Specialized Models on Small Fires (< {SMALL_FIRE_THRESHOLD_HA} ha) ---")
df_small = df[df['fire_area'] < SMALL_FIRE_THRESHOLD_HA].copy()

X_small = df_small[feature_cols]
y_small = np.log1p(df_small[target_col])

rf_small = RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42, n_jobs=-1).fit(X_small, y_small)
xgb_small = XGBRegressor(n_estimators=200, learning_rate=0.1, random_state=42, n_jobs=-1).fit(X_small, y_small)
cat_small = CatBoostRegressor(iterations=200, learning_rate=0.1, random_state=42, verbose=0).fit(X_small, y_small)

os.makedirs(SMALL_FIRE_MODEL_DIR, exist_ok=True)
joblib.dump(rf_small, os.path.join(SMALL_FIRE_MODEL_DIR, 'randomforest_small_model.joblib'))
joblib.dump(xgb_small, os.path.join(SMALL_FIRE_MODEL_DIR, 'xgboost_small_model.joblib'))
joblib.dump(cat_small, os.path.join(SMALL_FIRE_MODEL_DIR, 'catboost_small_model.joblib'))
print("Specialized small-fire models trained and saved.")

print("\nModel training process complete.")