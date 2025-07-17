# -*- coding: utf-8 -*-
"""
This script performs simplified feature engineering on the corrected dataset.
It loads the data, creates high-value interaction features, and saves the result.
"""
import pandas as pd
import os

# --- Configuration ---
CWD = '/Users/heejunida/Desktop/kg/wildFire1/wild_fire_project/wild_fire_client'
INPUT_PATH = os.path.join(CWD, 'preprocess/csv/final_data_with_features_with_correct_duration_time.csv')
OUTPUT_PATH = os.path.join(CWD, 'final_data_interaction_features.csv')

# --- 1. Load Data ---
print(f"Loading data from {INPUT_PATH}...")
try:
    df = pd.read_csv(INPUT_PATH)
except FileNotFoundError:
    print(f"Error: Dataset not found at '{INPUT_PATH}'. Please ensure the file exists.")
    exit()

# --- 2. Create Interaction Features ---
print("Creating interaction features...")

# Interaction between weather and topography
df['wind_x_slope'] = df['WS10M_mean'] * df['slope']

# Combined weather conditions
df['temp_x_humidity'] = df['T2M_mean'] * df['RH2M_mean']

# Effect of wind over the fire's duration
df['duration_x_wind'] = df['fire_duration_hours'] * df['WS10M_mean']

print("New features created: 'wind_x_slope', 'temp_x_humidity', 'duration_x_wind'")

# --- 3. Save New DataFrame ---
df.to_csv(OUTPUT_PATH, index=False)
print(f"Successfully saved new feature set to {OUTPUT_PATH}")
