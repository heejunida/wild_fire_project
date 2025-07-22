import pandas as pd
import requests
import datetime
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

FIRE_CSV = "gangwon_fire_ml_input.csv"
OUT_CSV = "fire_weather_start_only.csv"  # Output file changed
API_SLEEP = 0.1  # Can be faster as we make fewer requests per fire
MAX_WORKERS = 10

# Global cache
weather_cache = {}
precip_cache = {}

def fetch_nasa_hourly_weather(lat, lng, yyyymmdd, hour_str, max_retry=3):
    """Fetches hourly weather data for a single point in time from NASA POWER."""
    cache_key = (lat, lng, yyyymmdd, hour_str)
    if cache_key in weather_cache:
        return weather_cache[cache_key]
    
    url = (
        f"https://power.larc.nasa.gov/api/temporal/hourly/point?"
        "parameters=T2M,RH2M,WS2M,WD2M,PRECTOTCORR,PS,ALLSKY_SFC_SW_DWN,WS10M,WD10M"
        f"&community=RE&longitude={lng}&latitude={lat}&start={yyyymmdd}&end={yyyymmdd}&format=JSON"
    )
    
    for attempt in range(max_retry):
        try:
            res = requests.get(url, timeout=20)
            res.raise_for_status()
            data = res.json().get("properties", {}).get("parameter", {})
            hour_key = f"{yyyymmdd}{hour_str.zfill(2)}"
            
            result = {
                "T2M": data.get("T2M", {}).get(hour_key, np.nan),
                "RH2M": data.get("RH2M", {}).get(hour_key, np.nan),
                "WS2M": data.get("WS2M", {}).get(hour_key, np.nan),
                "WD2M": data.get("WD2M", {}).get(hour_key, np.nan),
                "WS10M": data.get("WS10M", {}).get(hour_key, np.nan),
                "WD10M": data.get("WD10M", {}).get(hour_key, np.nan),
                "PRECTOTCORR": data.get("PRECTOTCORR", {}).get(hour_key, np.nan),
                "PS": data.get("PS", {}).get(hour_key, np.nan),
                "ALLSKY_SFC_SW_DWN": data.get("ALLSKY_SFC_SW_DWN", {}).get(hour_key, np.nan)
            }
            weather_cache[cache_key] = result
            return result
        except Exception as e:
            print(f"NASA API failed (Attempt {attempt+1}/{max_retry}): {e}")
            time.sleep(2)
            
    # Return NaN dict if all retries fail
    weather_cache[cache_key] = {k: np.nan for k in ["T2M","RH2M","WS2M","WD2M","WS10M","WD10M","PRECTOTCORR","PS","ALLSKY_SFC_SW_DWN"]}
    return weather_cache[cache_key]

def fetch_nasa_daily_precip(lat, lng, start_date, end_date, max_retry=3):
    """Fetches daily precipitation data for a date range."""
    cache_key = (lat, lng, start_date, end_date)
    if cache_key in precip_cache:
        return precip_cache[cache_key]
        
    url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters=PRECTOTCORR&community=RE&longitude={lng}&latitude={lat}"
        f"&start={start_date}&end={end_date}&format=JSON"
    )
    
    for attempt in range(max_retry):
        try:
            res = requests.get(url, timeout=20)
            res.raise_for_status()
            data = res.json().get("properties", {}).get("parameter", {}).get("PRECTOTCORR", {})
            precip_cache[cache_key] = data
            return data
        except Exception as e:
            print(f"NASA Daily Precip API failed (Attempt {attempt+1}/{max_retry}): {e}")
            time.sleep(2)
            
    precip_cache[cache_key] = {}
    return {}

def get_start_hour(timestr):
    """Extracts the hour from a time string, defaulting to 12 if invalid."""
    if pd.isnull(timestr) or not isinstance(timestr, str):
        return 12
    try:
        return int(timestr.split(":")[0])
    except (ValueError, IndexError):
        return 12

def calculate_precip_features(lat, lng, dt, periods=[7, 14, 30, 60, 90]):
    """Calculates cumulative precipitation and dry day features."""
    features = {}
    end_date_str = dt.strftime("%Y%m%d")
    
    # Fetch data for the longest period once
    longest_period = max(periods)
    start_date_str = (dt - datetime.timedelta(days=longest_period - 1)).strftime("%Y%m%d")
    precip_data = fetch_nasa_daily_precip(lat, lng, start_date_str, end_date_str)
    
    if not precip_data:
        # If API fails, return NaN for all features
        for p in periods:
            features[f"total_precip_{p}d_start"] = np.nan
            features[f"dry_days_{p}d_start"] = np.nan
        features["consecutive_dry_days_start"] = np.nan
        return features

    # Create a complete date-indexed series
    all_days = pd.to_datetime(list(precip_data.keys()), format='%Y%m%d')
    precip_series = pd.Series(precip_data.values(), index=all_days).sort_index()
    
    # Calculate features for each period
    for p in periods:
        start_date_period = dt - datetime.timedelta(days=p - 1)
        period_data = precip_series.loc[start_date_period:dt]
        
        features[f"total_precip_{p}d_start"] = period_data.sum()
        features[f"dry_days_{p}d_start"] = (period_data < 1).sum()

    # Calculate consecutive dry days
    consecutive_dry_days = 0
    for i in range(len(precip_series) - 1, -1, -1):
        if precip_series.iloc[i] < 1:
            consecutive_dry_days += 1
        else:
            break
    features["consecutive_dry_days_start"] = consecutive_dry_days
    
    return features

def process_single_fire(fire_row):
    """
    Processes one fire event to get start-time weather and precipitation features.
    """
    lat = fire_row['lat']
    lng = fire_row['lng']
    
    start_hour = get_start_hour(fire_row['starttime'])
    start_dt = datetime.datetime(
        int(fire_row['startyear']), 
        int(fire_row['startmonth']), 
        int(fire_row['startday']), 
        start_hour
    )
    
    end_hour = get_start_hour(fire_row['endtime'])
    end_dt = datetime.datetime(
        int(fire_row['endyear']), 
        int(fire_row['endmonth']), 
        int(fire_row['endday']), 
        end_hour
    )
    
    # Calculate fire duration
    duration_hours = (end_dt - start_dt).total_seconds() / 3600
    
    # --- 1. Get weather only at the start time (t=0) ---
    start_yyyymmdd = start_dt.strftime("%Y%m%d")
    start_hour_str = start_dt.strftime("%H")
    
    weather_at_start = fetch_nasa_hourly_weather(lat, lng, start_yyyymmdd, start_hour_str)
    
    # Prefix weather keys with `_0h` to match ML script's expectations
    weather_features = {f"{key}_0h": val for key, val in weather_at_start.items()}

    # --- 2. Calculate precipitation features based on the start date ---
    precip_features = calculate_precip_features(lat, lng, start_dt)
    
    # --- 3. Combine all data into a single dictionary ---
    row_data = fire_row.to_dict()
    row_data.update(weather_features)
    row_data.update(precip_features)
    row_data["fire_duration_hours"] = duration_hours if duration_hours > 0 else 0
    
    time.sleep(API_SLEEP)
    return row_data

if __name__ == "__main__":
    df = pd.read_csv(FIRE_CSV, encoding="utf-8-sig")
    result_rows = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Create a list of futures
        futures = [executor.submit(process_single_fire, row) for _, row in df.iterrows()]
        
        # Process futures as they complete
        for i, future in enumerate(as_completed(futures)):
            try:
                result = future.result()
                result_rows.append(result)
                print(f"[{i+1}/{len(df)}] Processed fire event.")
            except Exception as e:
                # It's useful to know which row failed, though we don't have its index directly
                print(f"Error processing a fire event: {e}")

    # Create DataFrame and save to new CSV
    final_df = pd.DataFrame(result_rows)
    final_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\nProcessing complete. Data saved to: {OUT_CSV}")