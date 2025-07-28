import requests
import datetime
import sys
import json
import numpy as np
import traceback
import time

# --- Centralized NASA POWER API Parameters ---
NASA_HOURLY_PARAMS = "T2M,RH2M,WS2M,WD2M,PRECTOTCORR,PS,ALLSKY_SFC_SW_DWN,WS10M,WD10M"
NASA_DAILY_PRECIP_PARAM = "PRECTOTCORR"

# --- FIX: New helper function to make the output JSON-compliant ---
def replace_nan_with_none(obj):
    """
    Recursively traverses a dictionary or list and replaces numpy.nan 
    with None, making it compatible with strict JSON parsers.
    """
    if isinstance(obj, dict):
        return {k: replace_nan_with_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_nan_with_none(elem) for elem in obj]
    # Check for numpy's NaN, including different types (e.g., float64, float32)
    elif isinstance(obj, (np.floating, float)) and np.isnan(obj):
        return None
    return obj

def _fetch_nasa_power_data(lat, lng, start_date, end_date, time_interval, parameters, max_retry=3, timeout=30):
    """Generic function to fetch data from the NASA POWER API with retries."""
    base_url = "https://power.larc.nasa.gov/api/temporal"
    url = (
        f"{base_url}/{time_interval}/point?"
        f"parameters={parameters}"
        f"&community=RE&longitude={lng}&latitude={lat}&start={start_date}&end={end_date}&format=JSON"
    )
    for attempt in range(max_retry):
        try:
            res = requests.get(url, timeout=timeout)
            res.raise_for_status()
            return res.json().get("properties", {}).get("parameter", {})
        except requests.exceptions.RequestException as e:
            # This print goes to stderr, which is not captured by the Java stdout reader
            print(f"Attempt {attempt + 1}/{max_retry} failed for {url}: {e}", file=sys.stderr)
            if attempt < max_retry - 1:
                time.sleep(2 ** attempt)
            else:
                raise e

def make_precip_features(lat, lng, end_dt, periods=[7, 14, 30, 60, 90]):
    """Creates long-term precipitation features."""
    res = {}
    dt_str = end_dt.strftime("%Y%m%d")
    for ndays in periods:
        sdate = (end_dt - datetime.timedelta(days=ndays - 1)).strftime("%Y%m%d")
        precip_data = _fetch_nasa_power_data(lat, lng, sdate, dt_str, "daily", NASA_DAILY_PRECIP_PARAM)
        precip_dict = precip_data.get(NASA_DAILY_PRECIP_PARAM, {})
        
        vals = [float(precip_dict.get((end_dt - datetime.timedelta(days=i)).strftime("%Y%m%d"), np.nan)) for i in range(ndays)][::-1]
        arr = np.array(vals, dtype=float)
        res[f"total_precip_{ndays}d_start"] = float(np.nansum(arr))
        res[f"dry_days_{ndays}d_start"] = int(np.sum(arr < 1))
    
    cons = 0
    for v in arr[::-1]:
        if np.isnan(v) or v < 1:
            cons += 1
        else:
            break
    res["consecutive_dry_days_start"] = int(cons)
    return res

if __name__ == "__main__":
    try:
        lat = float(sys.argv[1])
        lng = float(sys.argv[2])
        fire_date_str_from_java = sys.argv[3] 
        fire_time_hour = int(sys.argv[4])
        fire_date_dt = datetime.datetime.strptime(fire_date_str_from_java, "%Y%m%d")
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"Argument parsing failed: {e}. Usage: python fetch_all_weather.py lat lng yyyymmdd fire_time_hour"
        }))
        sys.exit(1)

    try:
        precip = make_precip_features(lat, lng, fire_date_dt)

        start_fetch_dt = fire_date_dt - datetime.timedelta(days=1)
        end_fetch_dt = fire_date_dt + datetime.timedelta(days=1)
        start_fetch_str = start_fetch_dt.strftime("%Y%m%d")
        end_fetch_str = end_fetch_dt.strftime("%Y%m%d")

        hourly_data_raw = _fetch_nasa_power_data(
            lat, lng, start_fetch_str, end_fetch_str, "hourly", NASA_HOURLY_PARAMS
        )

        weather_timeseries = []
        current_dt = start_fetch_dt
        while current_dt <= end_fetch_dt:
            for hour in range(24):
                key = (current_dt + datetime.timedelta(hours=hour)).strftime("%Y%m%d%H")
                hourly_point = {"dt_str": key}
                for param, data_dict in hourly_data_raw.items():
                    val = data_dict.get(key, np.nan)
                    hourly_point[param] = np.nan if val == -999 else float(val)
                weather_timeseries.append(hourly_point)
            current_dt += datetime.timedelta(days=1)

        result = {
            "lat": lat,
            "lng": lng,
            "fire_date": fire_date_dt.strftime("%Y-%m-%d"),
            "fire_time_hour": fire_time_hour,
            **precip,
            "weather_timeseries": weather_timeseries,
            "success": True
        }
        
        # --- FIX: Sanitize the final dictionary before printing ---
        clean_result = replace_nan_with_none(result)
        
        print(json.dumps(clean_result))

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }))
        sys.exit(1)
