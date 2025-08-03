import pandas as pd
import numpy as np
import sys
import os
import json
import datetime
from scipy.stats import linregress

# Add the parent directory to the Python path to find the 'util' module.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.fwi_calc import fwi_calc

# Suppress PerformanceWarning for cleaner output.
import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

EPS = 1e-6  # To prevent zero division

def create_trend_features(hourly_values):
    """Calculates mean, std, min, max, and trend (slope) for a list of values."""
    if not hourly_values or len(hourly_values) < 2:
        return {'mean': np.nan, 'std': np.nan, 'min': np.nan, 'max': np.nan, 'trend': np.nan}
    
    arr = np.array(hourly_values, dtype=float)
    arr_no_nan = arr[~np.isnan(arr)]
    if arr_no_nan.size < 2:
        return {'mean': np.nan, 'std': np.nan, 'min': np.nan, 'max': np.nan, 'trend': np.nan}

    time_axis = np.arange(len(arr))
    mask = ~np.isnan(arr)
    slope = linregress(time_axis[mask], arr[mask]).slope if np.sum(mask) >= 2 else 0.0

    return {
        'mean': np.mean(arr_no_nan),
        'std': np.std(arr_no_nan),
        'min': np.min(arr_no_nan),
        'max': np.max(arr_no_nan),
        'trend': slope
    }

def calculate_fwi_components(row, hour=None):
    """Calculates all FWI components for a given row and time step."""
    try:
        prefix = f"T2M_{hour}h" if hour is not None else "T2M_0h"
        T = row.get(f'T2M_{hour}h' if hour is not None else 'T2M_0h', np.nan)
        RH = row.get(f'RH2M_{hour}h' if hour is not None else 'RH2M_0h', np.nan)
        W = row.get(f'WS10M_{hour}h' if hour is not None else 'WS10M_0h', np.nan)
        P = row.get(f'PRECTOTCORR_{hour}h' if hour is not None else 'PRECTOTCORR_0h', 0)
        month = row.get('fire_month', 6)

        if pd.isna(T) or pd.isna(RH) or pd.isna(W):
            return {comp: np.nan for comp in ['FFMC', 'DMC', 'DC', 'ISI', 'BUI', 'FWI']}

        return fwi_calc(T=T, RH=RH, W=W, P=P, month=month, FFMC0=85, DMC0=6, DC0=15)
    except Exception:
        return {comp: np.nan for comp in ['FFMC', 'DMC', 'DC', 'ISI', 'BUI', 'FWI']}

def feature_engineer_from_json(input_json):
    """
    Takes a JSON object, engineers features, and returns a JSON object.
    """
    # --- FIX 1: Immediately convert JSON to a DataFrame ---
    df = pd.DataFrame([input_json])

    # --- FIX 2: Validate essential inputs ---
    if 'fire_date' not in df.columns or 'fire_time_hour' not in df.columns:
        raise ValueError("Input JSON must contain 'fire_date' and 'fire_time_hour'.")
    if 'weather_timeseries' not in df.columns or not isinstance(df.iloc[0]['weather_timeseries'], list) or not df.iloc[0]['weather_timeseries']:
        raise ValueError("'weather_timeseries' is missing, not a list, or is empty.")

    # --- Process Weather Timeseries ---
    fire_time_hour = df.iloc[0]['fire_time_hour']
    fire_date_str = df.iloc[0]['fire_date']
    fire_dt = datetime.datetime.strptime(f"{fire_date_str} {fire_time_hour}:00", "%Y-%m-%d %H:%M")

    weather_df = pd.DataFrame(df.iloc[0]['weather_timeseries'])
    weather_df['dt'] = pd.to_datetime(weather_df['dt_str'], format='%Y%m%d%H')

    # Isolate Ignition-Time (_0h) Weather
    ignition_weather = weather_df[weather_df['dt'] == fire_dt]
    if not ignition_weather.empty:
        ignition_features = ignition_weather.drop(columns=['dt_str', 'dt']).rename(columns=lambda c: f"{c}_0h")
        for col, value in ignition_features.iloc[0].items():
            df[col] = value

    # Create Historical Trend Features (Past 24h)
    past_weather = weather_df[(weather_df['dt'] >= fire_dt - datetime.timedelta(hours=24)) & (weather_df['dt'] < fire_dt)]
    if not past_weather.empty:
        for param in ['T2M', 'RH2M', 'WS10M']:
            stats = create_trend_features(past_weather[param].tolist())
            for stat_name, stat_value in stats.items():
                df[f'{param.lower()}_{stat_name}_past_24h'] = stat_value

    # Create Forecast Trend Features (Next 12h)
    future_weather = weather_df[(weather_df['dt'] > fire_dt) & (weather_df['dt'] <= fire_dt + datetime.timedelta(hours=12))]
    if not future_weather.empty:
        for param in ['T2M', 'RH2M', 'WS10M']:
            stats = create_trend_features(future_weather[param].tolist())
            for stat_name, stat_value in stats.items():
                df[f'{param.lower()}_{stat_name}_forecast_12h'] = stat_value
    
    df = df.drop(columns=['weather_timeseries'])

    # --- Derive Date/Time & Seasonal Features ---
    fire_datetime = pd.to_datetime(df['fire_date'])
    df['startyear'] = fire_datetime.dt.year
    df['startmonth'] = fire_datetime.dt.month
    df['startday'] = fire_datetime.dt.day
    df['fire_month'] = fire_datetime.dt.month
    df['is_spring'] = df['fire_month'].isin([3, 4, 5]).astype(int)
    df['is_autumn'] = df['fire_month'].isin([9, 10, 11]).astype(int)

    # --- Calculate FWI ---
    # --- DEBUG: Print FWI input values ---
    print("--- FWI Calculation Inputs ---", file=sys.stderr)
    print(df[['T2M_0h', 'RH2M_0h', 'WS10M_0h', 'PRECTOTCORR_0h', 'fire_month']].iloc[0], file=sys.stderr)
    print("------------------------------", file=sys.stderr)
    
    fwi_results = df.apply(lambda row: calculate_fwi_components(row, hour=0), axis=1)
    df = pd.concat([df, pd.DataFrame(fwi_results.tolist()).add_suffix('_0h')], axis=1)

    # --- FIX 3: Safe Feature Engineering ---
    # Use .get() with a default value to prevent errors if a column is missing.
    df['dry_windy_combo'] = df.get('dry_days_30d_start', 0) * df.get('WS10M_0h', 0)
    df['hot_dry_combo'] = df.get('T2M_0h', 0) / (df.get('RH2M_0h', 100) + EPS)
    df['fuel_combo'] = df.get('treecover_pre_fire_5x5', 0) * df.get('ndvi_before', 0)
    df['slope_south_combo'] = df.get('slope_mean', 0) * df.get('aspect_south_ratio', 0)
    df['potential_spread_index'] = df['dry_windy_combo'] * df['fuel_combo']
    df['terrain_var_effect'] = df.get('elevation_std', 0) + df.get('slope_std', 0)
    df['south_steep_effect'] = df.get('slope_max', 0) * df.get('aspect_south_ratio', 0)
    df['dry_to_rain_ratio_30d'] = df.get('dry_days_30d_start', 0) / (df.get('total_precip_30d_start', 0) + EPS)
    df['ndvi_stress'] = 0.7 - df.get('ndvi_before', 0.7)
    
    # Flags with safe checks
    df['high_wind_flag'] = (df.get('ws10m_max_forecast_12h', 0) > 7).astype(int)
    df['low_humidity_flag'] = (df.get('rh2m_min_forecast_12h', 100) < 30).astype(int)
    df['extreme_hot_flag'] = (df.get('t2m_max_forecast_12h', 0) > 33).astype(int)

    # --- Final Cleanup ---
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(0) 
    
    final_dict = df.to_dict('records')[0]
    return final_dict

if __name__ == '__main__':
    try:
        input_json_str = sys.stdin.read()
        input_data = json.loads(input_json_str)
        engineered_data = feature_engineer_from_json(input_data)
        print(json.dumps(engineered_data, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Feature engineering failed: {str(e)}"}))
        sys.exit(1)