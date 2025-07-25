import requests
import datetime
import sys
import json
import numpy as np
import traceback
import time

# --- NEW: Centralized NASA POWER API Parameters ---
NASA_HOURLY_PARAMS = "T2M,RH2M,WS2M,WD2M,PRECTOTCORR,PS,ALLSKY_SFC_SW_DWN,WS10M,WD10M"
NASA_DAILY_PRECIP_PARAM = "PRECTOTCORR"

# --- NEW: Generic NASA POWER API Fetcher ---
def _fetch_nasa_power_data(lat, lng, start_date, end_date, time_interval, parameters, max_retry=3, timeout=30):
    base_url = "https://power.larc.nasa.gov/api/temporal"
    url = (
        f"{base_url}/{time_interval}/point?"
        f"parameters={parameters}"
        f"&community=RE&longitude={lng}&latitude={lat}&start={start_date}&end={end_date}&format=JSON"
    )
    for attempt in range(max_retry):
        try:
            res = requests.get(url, timeout=timeout)
            res.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
            return res.json().get("properties", {}).get("parameter", {})
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{max_retry} failed for {url}: {e}", file=sys.stderr)
            if attempt < max_retry - 1:
                time.sleep(2 ** attempt) # Exponential backoff
            else:
                raise e

def make_precip_features(lat, lng, end_dt, periods=[7,14,30,60,90]):
    res = {}
    dt_str = end_dt.strftime("%Y%m%d")
    for ndays in periods:
        sdate = (end_dt - datetime.timedelta(days=ndays-1)).strftime("%Y%m%d")
        # Use the new generic fetcher
        precip_data = _fetch_nasa_power_data(lat, lng, sdate, dt_str, "daily", NASA_DAILY_PRECIP_PARAM)
        precip_dict = precip_data.get(NASA_DAILY_PRECIP_PARAM, {})

        vals = [float(precip_dict.get((end_dt - datetime.timedelta(days=i)).strftime("%Y%m%d"), np.nan)) for i in range(ndays)][::-1]
        arr = np.array(vals, dtype=float)
        res[f"total_precip_{ndays}d_start"] = float(np.nansum(arr))
        res[f"dry_days_{ndays}d_start"] = int(np.sum(arr < 1))
    # 연속 무강수일수(최근부터 몇일째 비 안옴, 1mm 미만)
    cons = 0
    for v in arr[::-1]:
        if np.isnan(v) or v < 1:
            cons += 1
        else:
            break
    res[f"consecutive_dry_days_start"] = int(cons)
    return res

# Removed make_time_points function as it's no longer needed for fetching multiple hourly points

if __name__ == "__main__":
    try:
        lat = float(sys.argv[1])
        lng = float(sys.argv[2])
        start_yyyymmdd = sys.argv[3] # Day before fire
        end_yyyymmdd = sys.argv[4]   # Day of fire
        fire_time_hour = int(sys.argv[5])

        fire_date_dt = datetime.datetime.strptime(end_yyyymmdd, "%Y%m%d")
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"Argument parsing failed: {e}. Usage: python fetch_all_weather.py lat lng start_yyyymmdd end_yyyymmdd fire_time_hour"
        }, ensure_ascii=False))
        sys.exit(2)

    try:
        # 1. Fetch daily precipitation features (based on the fire date)
        precip = make_precip_features(lat, lng, fire_date_dt)

        # 2. Fetch all hourly weather data for the day before AND the day of the fire
        hourly_data_raw = _fetch_nasa_power_data(
            lat, lng, start_yyyymmdd, end_yyyymmdd,
            "hourly", NASA_HOURLY_PARAMS
        )

        # Structure the hourly data into a list of dictionaries
        weather_timeseries = []
        start_dt = datetime.datetime.strptime(start_yyyymmdd, "%Y%m%d")
        end_dt = datetime.datetime.strptime(end_yyyymmdd, "%Y%m%d")
        
        current_dt = start_dt
        while current_dt <= end_dt:
            for hour in range(24):
                key = (current_dt + datetime.timedelta(hours=hour)).strftime("%Y%m%d%H")
                hourly_point = {"dt_str": key}
                for param, data_dict in hourly_data_raw.items():
                    hourly_point[param] = data_dict.get(key, np.nan)
                weather_timeseries.append(hourly_point)
            current_dt += datetime.timedelta(days=1)

        # Combine all essential features into the final result
        result = {
            "lat": lat,
            "lng": lng,
            "fire_date": fire_date_dt.strftime("%Y-%m-%d"),
            "fire_time_hour": fire_time_hour,
            **precip,
            "weather_timeseries": weather_timeseries,
            "success": True
        }
        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, ensure_ascii=False))
        sys.exit(2)
