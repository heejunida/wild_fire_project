import pandas as pd
import numpy as np
import sys
import os
import argparse

# Add the utility function module path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.fwi_calc import fwi_calc

EPS = 1e-6  # To prevent zero division

def calculate_fwi_components(row, hour=None):
    """Calculates all FWI components for a given row and time step."""
    try:
        # If hour is specified, use f-string to get the correct column name
        if hour is not None:
            t_col, rh_col, w_col, p_col = f'T2M_{hour}h', f'RH2M_{hour}h', f'WS10M_{hour}h', f'PRECTOTCORR_{hour}h'
        else: # Default to 0h if no hour is specified
            t_col, rh_col, w_col, p_col = 'T2M_0h', 'RH2M_0h', 'WS10M_0h', 'PRECTOTCORR_0h'

        T = row.get(t_col, np.nan)
        RH = row.get(rh_col, np.nan)
        W = row.get(w_col, np.nan)
        P = row.get(p_col, 0) # Precipitation defaults to 0 if not present
        month = row.get('fire_month', 6)

        # Return a dictionary of NaNs if essential weather data is missing
        if pd.isna(T) or pd.isna(RH) or pd.isna(W):
            return {comp: np.nan for comp in ['FFMC', 'DMC', 'DC', 'ISI', 'BUI', 'FWI']}

        # Calculate FWI and return all components
        res = fwi_calc(T=T, RH=RH, W=W, P=P, month=month, FFMC0=85, DMC0=6, DC0=15)
        return res

    except Exception:
        # Return NaNs if any other error occurs
        return {comp: np.nan for comp in ['FFMC', 'DMC', 'DC', 'ISI', 'BUI', 'FWI']}

def feature_engineer(input_path, output_path):
    """
    Loads wildfire data, engineers a rich set of features, and saves the result.
    """
    # === 1. Load Data ===
    df = pd.read_csv(input_path)
    print(f"Loaded data with shape: {df.shape}")

    # === 2. Drop Unnecessary Columns ===
    drop_cols = [
        'gungu', 'eupmyeon', 'dongri', 'jibun', 'locsi', 'matched_address',
        'lat', 'lng',
    ]
    df = df.drop(columns=[col for col in drop_cols if col in df.columns])

    # === 3. Handle Missing Weather Data (0.0 -> NaN) ===
    weather_cols = [
        col for col in df.columns
        if any(x in col for x in ['T2M_', 'RH2M_', 'WS2M_', 'WS10M_', 'PRECTOTCORR_', 'WD2M_', 'WD10M_'])
    ]
    for col in weather_cols:
        df[col] = df[col].replace(0.0, np.nan)

    # === 4. Derive Seasonal Features ===
    if 'fire_date' in df.columns:
        df['fire_month'] = pd.to_datetime(df['fire_date']).dt.month
        df['is_spring'] = df['fire_month'].isin([3, 4, 5]).astype(int)
        df['is_autumn'] = df['fire_month'].isin([9, 10, 11]).astype(int)
        df = df.drop(columns=['fire_date'])
        print("Derived seasonal features.")

    # === 5. Calculate FWI and its components for 0h and means ===
    try:
        # Calculate for 0h
        fwi_0h_results = df.apply(lambda row: calculate_fwi_components(row, hour=0), axis=1)
        fwi_0h_df = pd.DataFrame(fwi_0h_results.tolist()).add_suffix('_0h')
        df = pd.concat([df, fwi_0h_df], axis=1)
        print("Calculated FWI components for 0h.")

        # Calculate for mean over 0-12h
        fwi_components = ['FFMC', 'DMC', 'DC', 'ISI', 'BUI', 'FWI']
        fwi_hourly_dfs = []
        for h in [0, 3, 6, 9, 12]:
            if f'T2M_{h}h' in df.columns:
                hourly_results = df.apply(lambda row: calculate_fwi_components(row, hour=h), axis=1)
                hourly_df = pd.DataFrame(hourly_results.tolist()).add_suffix(f'_{h}h')
                fwi_hourly_dfs.append(hourly_df)

        if fwi_hourly_dfs:
            # Concatenate all hourly FWI dataframes
            full_hourly_fwi = pd.concat(fwi_hourly_dfs, axis=1)
            # Calculate the mean for each component across the time steps
            for comp in fwi_components:
                comp_cols = [f'{comp}_{h}h' for h in [0, 3, 6, 9, 12] if f'{comp}_{h}h' in full_hourly_fwi.columns]
                if comp_cols:
                    df[f'{comp}_mean_0_12h'] = full_hourly_fwi[comp_cols].mean(axis=1)
            print("Calculated mean FWI components for 0-12h.")

    except ImportError:
        print("Warning: 'fwi_calc' not found. Skipping FWI feature generation.")
    except Exception as e:
        print(f"An error occurred during FWI calculation: {e}")


    # === 6. Basic Feature Engineering ===
    df['dry_windy_combo'] = df['dry_days_30d_start'] * df.get('WS10M_0h', np.nan)
    df['hot_dry_combo'] = df.get('T2M_0h', np.nan) / (df.get('RH2M_0h', np.nan) + EPS)
    df['fuel_combo'] = df['treecover_pre_fire_5x5'] * df['ndvi_before']
    df['slope_south_combo'] = df['slope_mean'] * df['aspect_south_ratio']
    df['potential_spread_index'] = df['dry_windy_combo'] * df['fuel_combo']
    df['terrain_var_effect'] = df['elevation_std'] + df['slope_std']
    df['south_steep_effect'] = df['slope_max'] * df['aspect_south_ratio']
    print("Created basic interaction features.")

    # === 7. Climate Time-Series Variability (0-12h) ===
    for var in ['WS10M', 'T2M', 'RH2M', 'WD10M']:
        cols = [f"{var}_{h}h" for h in [0, 3, 6, 9, 12] if f"{var}_{h}h" in df.columns]
        if len(cols) >= 2:
            df[f"{var}_std_0_12h"] = df[cols].std(axis=1)

    # === 8. Max/Min Value Features ===
    ws_cols = [f'WS10M_{h}h' for h in [0, 3, 6, 9, 12] if f'WS10M_{h}h' in df.columns]
    rh_cols = [f'RH2M_{h}h' for h in [0, 3, 6, 9, 12] if f'RH2M_{h}h' in df.columns]
    t2m_cols = [f'T2M_{h}h' for h in [0, 3, 6, 9, 12] if f'T2M_{h}h' in df.columns]
    if ws_cols: df['max_wind_0_12h'] = df[ws_cols].max(axis=1)
    if rh_cols: df['min_humidity_0_12h'] = df[rh_cols].min(axis=1)
    if t2m_cols: df['max_temp_0_12h'] = df[t2m_cols].max(axis=1)
    print("Created variability and min/max features.")

    # === 9. Wind Consistency ===
    if 'WS10M_std_0_12h' in df.columns:
        wd_cols = [f'WD10M_{h}h' for h in [0, 3, 6, 9, 12] if f'WD10M_{h}h' in df.columns]
        if wd_cols:
            df['WD10M_var_0_12h'] = df[wd_cols].std(axis=1)
            df['wind_steady_flag'] = ((df['WS10M_std_0_12h'] < 2) & (df['WD10M_var_0_12h'] < 30)).astype(int)

    # === 10. Other Engineered Features ===
    df['dry_to_rain_ratio_30d'] = df['dry_days_30d_start'] / (df['total_precip_30d_start'] + EPS)
    df['ndvi_stress'] = 0.7 - df['ndvi_before'] # Assuming 0.7 is a healthy baseline
    df['high_wind_flag'] = (df.get('max_wind_0_12h', 0) > 7).astype(int)
    df['low_humidity_flag'] = (df.get('min_humidity_0_12h', 100) < 30).astype(int)
    df['extreme_hot_flag'] = (df.get('max_temp_0_12h', 0) > 33).astype(int)
    print("Created additional flag and ratio features.")

    # === 11. Handle NaN/Inf values ===
    df = df.replace([np.inf, -np.inf], np.nan)
    print(f"Replaced Inf values. Shape after all steps: {df.shape}")

    # === 12. Save the final dataset ===
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Feature engineering complete. Saved to '{output_path}'")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run the feature engineering pipeline for wildfire data.")
    parser.add_argument(
        '--input',
        type=str,
        default="gangwon_fire_dem_slope_aspect_window.csv",
        help="Path to the input CSV file."
    )
    parser.add_argument(
        '--output',
        type=str,
        default="final_merged_feature_engineered.csv",
        help="Path to save the output CSV file."
    )
    args = parser.parse_args()

    feature_engineer(args.input, args.output)