import numpy as np
import pandas as pd
import datetime
import requests
import os
import time
from scipy.stats import linregress

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_FILE = os.path.join(BASE_DIR, 'enriched_training_data.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, 'final_enriched_with_nasa.csv')
NASA_HOURLY_PARAMS = "T2M,RH2M,WS10M"

def fetch_nasa_hourly_timespan(lat, lng, start_dt, end_dt, max_retry=5, timeout=30):
    # 비교시 hour로만 비교하도록 window를 정규화 (분/초/마이크로초 0)
    start_dt_hour = start_dt.replace(minute=0, second=0, microsecond=0)
    end_dt_hour = end_dt.replace(minute=0, second=0, microsecond=0)
    hourly_results = {param: [] for param in NASA_HOURLY_PARAMS.split(',')}
    # 날짜 기준 범위 루프 (날짜별 API만 호출)
    curr_day = start_dt_hour.date()
    last_day = end_dt_hour.date()
    while curr_day <= last_day:
        day_str = curr_day.strftime("%Y%m%d")
        for attempt in range(max_retry):
            try:
                url = (
                    f"https://power.larc.nasa.gov/api/temporal/hourly/point?"
                    f"parameters={NASA_HOURLY_PARAMS}"
                    f"&community=RE&longitude={lng}&latitude={lat}&start={day_str}&end={day_str}&format=JSON"
                )
                res = requests.get(url, timeout=timeout)
                res.raise_for_status()
                nasa_json = res.json().get("properties", {}).get("parameter", {})
                for param in NASA_HOURLY_PARAMS.split(','):
                    vals = []
                    times = []
                    for h in range(24):
                        dt_key = f"{day_str}{str(h).zfill(2)}"
                        dt_actual = datetime.datetime.strptime(dt_key, "%Y%m%d%H")
                        if start_dt_hour <= dt_actual <= end_dt_hour:
                            v = nasa_json.get(param, {}).get(dt_key, np.nan)
                            vals.append(v)
                            times.append(dt_actual)
                            hourly_results[param].append(float(v) if v is not None else np.nan)
                    if vals:
                        print(f"[NASA RAW] {param} @ {day_str} : {vals} | {times}")
                break
            except Exception as e:
                if attempt < max_retry - 1:
                    time.sleep(2 ** attempt)
                else:
                    for h in range(24):
                        dt_key = f"{day_str}{str(h).zfill(2)}"
                        dt_actual = datetime.datetime.strptime(dt_key, "%Y%m%d%H")
                        if start_dt_hour <= dt_actual <= end_dt_hour:
                            for param in NASA_HOURLY_PARAMS.split(','):
                                hourly_results[param].append(np.nan)
        curr_day += datetime.timedelta(days=1)
    return hourly_results

def create_trend_features(hourly_values):
    if not hourly_values or len(hourly_values) < 2 or np.isnan(hourly_values).all():
        return {
            'mean': np.nan, 'std': np.nan, 'min': np.nan, 'max': np.nan, 'trend': np.nan,
            'range': np.nan, 'max_increase_1h': np.nan, 'max_decrease_1h': np.nan
        }
    arr = np.array(hourly_values)
    arr_no_nan = arr[~np.isnan(arr)]
    if arr_no_nan.size < 2:
        return {
            'mean': np.nan, 'std': np.nan, 'min': np.nan, 'max': np.nan, 'trend': np.nan,
            'range': np.nan, 'max_increase_1h': np.nan, 'max_decrease_1h': np.nan
        }
    mean_val = np.mean(arr_no_nan)
    std_val = np.std(arr_no_nan)
    min_val = np.min(arr_no_nan)
    max_val = np.max(arr_no_nan)
    time_axis = np.arange(len(arr))
    mask = ~np.isnan(arr)
    slope = linregress(time_axis[mask], arr[mask]).slope if np.sum(mask) >= 2 else 0.0
    diffs = np.diff(arr)
    return {
        'mean': mean_val,
        'std': std_val,
        'min': min_val,
        'max': max_val,
        'trend': slope,
        'range': max_val - min_val,
        'max_increase_1h': np.nanmax(diffs) if len(diffs) > 0 else 0,
        'max_decrease_1h': np.nanmin(diffs) if len(diffs) > 0 else 0
    }

def enrich_fire_event(row):
    try:
        s_time_str = str(row['starttime'])
        if pd.isna(row['starttime']):
            s_time_str = "1400"
        else:
            s_time_str = str(row['starttime']).replace(":", "")
            if len(s_time_str) > 4:
                s_time_str = s_time_str[:4]
            s_time_str = s_time_str.zfill(4)
        if pd.isna(row['startyear']) or pd.isna(row['startmonth']) or pd.isna(row['startday']):
            return pd.Series({})
        start_dt = datetime.datetime(
            int(row['startyear']), int(row['startmonth']), int(row['startday']),
            int(s_time_str[:2]), int(s_time_str[2:])
        )
        lat = row['start_latitude']
        lng = row['start_longitude']
        if pd.isna(lat) or pd.isna(lng):
            return pd.Series({})
        def floor_hour(dt):
            return dt.replace(minute=0, second=0, microsecond=0)
        
        # 정각 보정
        raw_past_start = start_dt - datetime.timedelta(hours=24)
        raw_past_end   = start_dt - datetime.timedelta(hours=1)
        past_start_dt  = floor_hour(raw_past_start)
        past_end_dt    = floor_hour(raw_past_end)
        raw_future_start = start_dt + datetime.timedelta(hours=1)
        raw_future_end   = start_dt + datetime.timedelta(hours=12)
        future_start_dt  = floor_hour(raw_future_start)
        future_end_dt    = floor_hour(raw_future_end)

        # fetch ("정각" 윈도우만 사용)
        past_hourly_values = fetch_nasa_hourly_timespan(lat, lng, past_start_dt, past_end_dt)
        future_hourly_values = fetch_nasa_hourly_timespan(lat, lng, future_start_dt, future_end_dt)
        print(f"[DEBUG][{row.name if hasattr(row, 'name') else ''}] start_dt: {start_dt}")
        print(f"[DEBUG] past: {past_start_dt} ~ {past_end_dt} ({(past_end_dt-past_start_dt).total_seconds()/3600+1} hours)")
        print(f"[DEBUG]   future: {future_start_dt} ~ {future_end_dt} ({(future_end_dt-future_start_dt).total_seconds()/3600+1} hours)")

        new_features = {}
        if past_hourly_values:
            for param, values in past_hourly_values.items():
                stats = create_trend_features(values)
                for stat_name, stat_value in stats.items():
                    fname = f'{param.lower()}_{stat_name}_past_24h'
                    new_features[fname] = stat_value
                    print(f"[FEAT] {fname} = {stat_value}")
        if future_hourly_values:
            for param, values in future_hourly_values.items():
                stats = create_trend_features(values)
                for stat_name, stat_value in stats.items():
                    fname = f'{param.lower()}_{stat_name}_forecast_12h'
                    new_features[fname] = stat_value
                    print(f"[FEAT] {fname} = {stat_value}")
        return pd.Series(new_features)
    except Exception as e:
        print(f"    - Error processing row: {e}")
        return pd.Series({})

if __name__ == '__main__':
    df = pd.read_csv(CLEAN_FILE, encoding='utf-8')
    print(f"Loaded {len(df)} rows from {CLEAN_FILE}")
    all_new_features = []
    for idx, row in df.iterrows():
        print(f"\n=== [Row {idx+1}] ===")
        new_features = enrich_fire_event(row)
        all_new_features.append(new_features)
        print(f"[ROW DONE] {idx+1}/{len(df)}\n")
    new_features_df = pd.DataFrame(all_new_features, index=df.index)
    df_final = pd.concat([df.reset_index(drop=True), new_features_df.reset_index(drop=True)], axis=1)
    df_final.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    print(f"✅ NASA enriched saved: {OUTPUT_FILE}")

# if __name__ == '__main__':
#     df = pd.read_csv(CLEAN_FILE, encoding='utf-8')
#     print(f"Loaded {len(df)} rows from {CLEAN_FILE}")
#     all_new_features = []
#     row_idx = 88   # (0부터 시작하므로 87이 88번째)
#     row = df.iloc[row_idx]
#     # print(f"\n=== [Row {idx+1}] ===")
#     print(f"\n=== [Row {row_idx}] ===")
#     new_features = enrich_fire_event(row)
#     all_new_features.append(new_features)
#     print(new_features)
#     # print(f"[ROW DONE] {idx+1}/{len(df)}\n")
#     new_features_df = pd.DataFrame(all_new_features, index=df.index)
#     df_final = pd.concat([df.reset_index(drop=True), new_features_df.reset_index(drop=True)], axis=1)
#     df_final.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
#     print(f"✅ NASA enriched saved: {OUTPUT_FILE}")