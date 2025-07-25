import pandas as pd
import numpy as np
import sys
import os
import json
import datetime
from scipy.stats import linregress

# --- CORRECT IMPORT LOGIC ---
# Add the parent directory ('wild_fire_client') to the Python path.
# This allows the script to find the 'util' module.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.fwi_calc import fwi_calc

# Suppress PerformanceWarning for a cleaner output in the pipeline
import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

EPS = 1e-6  # To prevent zero division

def create_trend_features(hourly_values):
    """Calculates mean, std, min, max, and trend (slope) for a list of values."""
    if not hourly_values or len(hourly_values) < 2 or np.isnan(hourly_values).all():
        return {'mean': np.nan, 'std': np.nan, 'min': np.nan, 'max': np.nan, 'trend': np.nan}
    
    arr = np.array(hourly_values)
    arr = arr[~np.isnan(arr)] # Remove NaNs for calculation
    if arr.size < 2:
         return {'mean': np.nan, 'std': np.nan, 'min': np.nan, 'max': np.nan, 'trend': np.nan}

    time_axis = np.arange(len(hourly_values))
    mask = ~np.isnan(hourly_values)
    if np.sum(mask) < 2:
        slope = 0.0
    else:
        slope = linregress(time_axis[mask], np.array(hourly_values)[mask]).slope

    return {
        'mean': np.mean(arr),
        'std': np.std(arr),
        'min': np.min(arr),
        'max': np.max(arr),
        'trend': slope
    }

def calculate_fwi_components(row, hour=None):
    """Calculates all FWI components for a given row and time step."""
    try:
        if hour is not None:
            t_col, rh_col, w_col, p_col = f'T2M_{hour}h', f'RH2M_{hour}h', f'WS10M_{hour}h', f'PRECTOTCORR_{hour}h'
        else:
            t_col, rh_col, w_col, p_col = 'T2M_0h', 'RH2M_0h', 'WS10M_0h', 'PRECTOTCORR_0h'

        T = row.get(t_col, np.nan)
        RH = row.get(rh_col, np.nan)
        W = row.get(w_col, np.nan)
        P = row.get(p_col, 0)
        month = row.get('fire_month', 6)

        if pd.isna(T) or pd.isna(RH) or pd.isna(W):
            return {comp: np.nan for comp in ['FFMC', 'DMC', 'DC', 'ISI', 'BUI', 'FWI']}

        res = fwi_calc(T=T, RH=RH, W=W, P=P, month=month, FFMC0=85, DMC0=6, DC0=15)
        return res
    except Exception:
        return {comp: np.nan for comp in ['FFMC', 'DMC', 'DC', 'ISI', 'BUI', 'FWI']}

def feature_engineer_from_json(input_json):
    """
    Takes a JSON object, engineers features, and returns a JSON object.
    """
    # === 1. Load Data from JSON into a DataFrame ===
    # === NEW: Handle the enriched weather_timeseries structure ===
    if 'weather_timeseries' in df.columns and isinstance(df.iloc[0]['weather_timeseries'], list):
        fire_time_hour = df.iloc[0].get('fire_time_hour', 14)
        fire_date_str = df.iloc[0].get('fire_date')
        fire_dt = datetime.datetime.strptime(f"{fire_date_str} {fire_time_hour}:00", "%Y-%m-%d %H:%M")

        weather_df = pd.DataFrame(df.iloc[0]['weather_timeseries'])
        weather_df['dt'] = pd.to_datetime(weather_df['dt_str'], format='%Y%m%d%H')

        # --- Isolate Ignition-Time (_0h) Weather ---
        ignition_weather = weather_df[weather_df['dt'] == fire_dt]
        if not ignition_weather.empty:
            ignition_features = ignition_weather.drop(columns=['dt_str', 'dt']).rename(columns=lambda c: f"{c}_0h")
            for col, value in ignition_features.iloc[0].items():
                df[col] = value

        # --- Create Historical Trend Features (Past 24h) ---
        past_start_dt = fire_dt - datetime.timedelta(hours=24)
        past_end_dt = fire_dt - datetime.timedelta(hours=1)
        past_weather = weather_df[(weather_df['dt'] >= past_start_dt) & (weather_df['dt'] <= past_end_dt)]
        
        if not past_weather.empty:
            for param in ['T2M', 'RH2M', 'WS10M']:
                stats = create_trend_features(past_weather[param].tolist())
                for stat_name, stat_value in stats.items():
                    df[f'{param.lower()}_{stat_name}_past_24h'] = stat_value

        # --- Create Forecast Trend Features (Next 12h) ---
        future_start_dt = fire_dt + datetime.timedelta(hours=1)
        future_end_dt = fire_dt + datetime.timedelta(hours=12)
        future_weather = weather_df[(weather_df['dt'] >= future_start_dt) & (weather_df['dt'] <= future_end_dt)]

        if not future_weather.empty:
            for param in ['T2M', 'RH2M', 'WS10M']:
                stats = create_trend_features(future_weather[param].tolist())
                for stat_name, stat_value in stats.items():
                    df[f'{param.lower()}_{stat_name}_forecast_12h'] = stat_value
        
        df = df.drop(columns=['weather_timeseries'])

    # Use 'fire_date' if it exists
    if 'fire_date' not in df.columns and 'start_dt' in df.columns:
        df['fire_date'] = pd.to_datetime(df['start_dt']).dt.strftime('%Y-%m-%d')
    
    # === 2. Handle Missing Weather Data (0.0 -> NaN) ===
    # This is less critical now but good practice
    weather_cols = [col for col in df.columns if any(x in col for x in ['T2M_', 'RH2M_', 'WS10M_'])]
    for col in weather_cols:
        df[col] = df[col].replace(0.0, np.nan)

    # === 3. Derive Date/Time & Seasonal Features ===
    if 'fire_date' in df.columns:
        fire_datetime = pd.to_datetime(df['fire_date'])
        df['startyear'] = fire_datetime.dt.year
        df['startmonth'] = fire_datetime.dt.month
        df['startday'] = fire_datetime.dt.day
        df['fire_month'] = fire_datetime.dt.month  # Keep for existing seasonal logic
        df['is_spring'] = df['fire_month'].isin([3, 4, 5]).astype(int)
        df['is_autumn'] = df['fire_month'].isin([9, 10, 11]).astype(int)

    # === 4. Calculate FWI and its components ===
    fwi_0h_results = df.apply(lambda row: calculate_fwi_components(row, hour=0), axis=1)
    fwi_0h_df = pd.DataFrame(fwi_0h_results.tolist()).add_suffix('_0h')
    df = pd.concat([df, fwi_0h_df], axis=1)

    fwi_components = ['FFMC', 'DMC', 'DC', 'ISI', 'BUI', 'FWI']
    fwi_hourly_dfs = []
    for h in [0, 3, 6, 9, 12]:
        if f'T2M_{h}h' in df.columns:
            hourly_results = df.apply(lambda row: calculate_fwi_components(row, hour=h), axis=1)
            hourly_df = pd.DataFrame(hourly_results.tolist()).add_suffix(f'_{h}h')
            fwi_hourly_dfs.append(hourly_df)

    if fwi_hourly_dfs:
        full_hourly_fwi = pd.concat(fwi_hourly_dfs, axis=1)
        for comp in fwi_components:
            comp_cols = [f'{comp}_{h}h' for h in [0, 3, 6, 9, 12] if f'{comp}_{h}h' in full_hourly_fwi.columns]
            if comp_cols:
                df[f'{comp}_mean_0_12h'] = full_hourly_fwi[comp_cols].mean(axis=1)

    # === 5. Basic Feature Engineering ===
    df['dry_windy_combo'] = df['dry_days_30d_start'] * df.get('WS10M_0h', np.nan)
    df['hot_dry_combo'] = df.get('T2M_0h', np.nan) / (df.get('RH2M_0h', np.nan) + EPS)
    df['fuel_combo'] = df['treecover_pre_fire_5x5'] * df['ndvi_before']
    df['slope_south_combo'] = df['slope_mean'] * df['aspect_south_ratio']
    df['potential_spread_index'] = df['dry_windy_combo'] * df['fuel_combo']
    df['terrain_var_effect'] = df['elevation_std'] + df['slope_std']
    df['south_steep_effect'] = df['slope_max'] * df['aspect_south_ratio']

    # === 6. Climate Time-Series Variability (0-12h) ===
    for var in ['WS10M', 'T2M', 'RH2M', 'WD10M']:
        cols = [f"{var}_{h}h" for h in [0, 3, 6, 9, 12] if f"{var}_{h}h" in df.columns]
        if len(cols) >= 2:
            df[f"{var}_std_0_12h"] = df[cols].std(axis=1)

    ws_cols = [f'WS10M_{h}h' for h in [0, 3, 6, 9, 12] if f'WS10M_{h}h' in df.columns]
    rh_cols = [f'RH2M_{h}h' for h in [0, 3, 6, 9, 12] if f'RH2M_{h}h' in df.columns]
    t2m_cols = [f'T2M_{h}h' for h in [0, 3, 6, 9, 12] if f'T2M_{h}h' in df.columns]
    if ws_cols: df['max_wind_0_12h'] = df[ws_cols].max(axis=1)
    if rh_cols: df['min_humidity_0_12h'] = df[rh_cols].min(axis=1)
    if t2m_cols: df['max_temp_0_12h'] = df[t2m_cols].max(axis=1)

    df['wind_steady_flag'] = 0
    if 'WS10M_std_0_12h' in df.columns:
        wd_cols = [f'WD10M_{h}h' for h in [0, 3, 6, 9, 12] if f'WD10M_{h}h' in df.columns]
        if wd_cols:
            df['WD10M_var_0_12h'] = df[wd_cols].std(axis=1)
            df['wind_steady_flag'] = ((df['WS10M_std_0_12h'] < 2) & (df['WD10M_var_0_12h'] < 30)).astype(int)

    df['dry_to_rain_ratio_30d'] = df['dry_days_30d_start'] / (df['total_precip_30d_start'] + EPS)
    df['ndvi_stress'] = 0.7 - df['ndvi_before']
    df['high_wind_flag'] = (df['max_wind_0_12h'] > 7).astype(int) if 'max_wind_0_12h' in df.columns else 0
    df['low_humidity_flag'] = (df['min_humidity_0_12h'] < 30).astype(int) if 'min_humidity_0_12h' in df.columns else 0
    df['extreme_hot_flag'] = (df['max_temp_0_12h'] > 33).astype(int) if 'max_temp_0_12h' in df.columns else 0

    # === 7. One-Hot Encode Land Cover ===
    # The 'land_cover_name' is a categorical feature. We need to convert it to
    # a numerical format for the model. pd.get_dummies is perfect for this.
    if 'land_cover_name' in df.columns:
        # This will create new columns like 'land_cover_name_Grasslands', 'land_cover_name_Mixed Forests', etc.
        # The original 'land_cover_name' column is dropped automatically.
        df = pd.get_dummies(df, columns=['land_cover_name'], prefix='land_cover')

    # === 8. Handle NaN/Inf and Convert to Dictionary ===
    # The dataframe `df` now contains the original, weather, and all engineered features.
    # We just need to fill any remaining NaN/Inf values and convert to a dictionary.
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(0) 
    
    # Convert the single row DataFrame to the final dictionary. This is the single
    # source of truth for all features.
    final_dict = df.to_dict('records')[0]
    
    return final_dict

if __name__ == '__main__':
    # Read the JSON string from standard input
    input_json_str = sys.stdin.read()
    
    try:
        input_data = json.loads(input_json_str)
        # Run the feature engineering
        engineered_data = feature_engineer_from_json(input_data)
        # Print the final JSON to be captured by the Java servlet
        print(json.dumps(engineered_data, ensure_ascii=False))
    except Exception as e:
        # Print a structured error if anything goes wrong
        print(json.dumps({"error": f"Feature engineering failed: {str(e)}"}))
        sys.exit(1)
