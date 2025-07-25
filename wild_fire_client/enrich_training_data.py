import pandas as pd
import numpy as np
import datetime
import time
import requests
import sys
import re
import os
from scipy.stats import linregress

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, 'final_merged_feature_engineered.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, 'enriched_training_data.csv')
NASA_HOURLY_PARAMS = "T2M,RH2M,WS10M"

def fetch_nasa_hourly_timespan(lat, lng, start_dt, end_dt, max_retry=5, timeout=30):
    """
    특정 위경도, 시간 범위(start_dt ~ end_dt)에 대해,
    실제 필요 시간(YYYYMMDDHH)만 정확하게 추출해서 리턴.
    (날짜가 바뀌면 API 여러 번 호출해서 merge)
    """
    hourly_results = {param: [] for param in NASA_HOURLY_PARAMS.split(',')}
    curr_dt = start_dt
    while curr_dt <= end_dt:
        day = curr_dt.strftime("%Y%m%d")
        # 이 날짜(하루치)를 API로 가져오기
        for attempt in range(max_retry):
            try:
                url = (
                    f"https://power.larc.nasa.gov/api/temporal/hourly/point?"
                    f"parameters={NASA_HOURLY_PARAMS}"
                    f"&community=RE&longitude={lng}&latitude={lat}&start={day}&end={day}&format=JSON"
                )
                res = requests.get(url, timeout=timeout)
                res.raise_for_status()
                nasa_json = res.json().get("properties", {}).get("parameter", {})
                print(f"[DEBUG] {day} T2M 00시 값: {nasa_json.get('T2M', {}).get(day+'00', '없음')}")
                # 해당 날짜에 필요한 시간만 뽑기 (00~23시 중에서 우리가 원하는 구간만)
                for h in range(24):
                    dt_key = f"{day}{str(h).zfill(2)}"
                    print(f"[DEBUG] Try dt_key: {dt_key}")
                    if start_dt <= datetime.datetime.strptime(dt_key, "%Y%m%d%H") <= end_dt:
                        for param in NASA_HOURLY_PARAMS.split(','):
                            v = nasa_json.get(param, {}).get(dt_key, np.nan)
                            hourly_results[param].append(float(v) if v is not None else np.nan)
                break # 성공하면 retry 루프 탈출
            except requests.exceptions.RequestException as e:
                print(f"    - API Request failed [{day}] (attempt {attempt + 1}/{max_retry}): {e}", file=sys.stderr)
                if attempt < max_retry - 1:
                    time.sleep(2 ** attempt)
                else:
                    print(f"    - FINAL FAILED REQUEST for {url}", file=sys.stderr)
                    # 해당 날짜의 모든 시간대 NaN으로 채우기
                    for h in range(24):
                        dt_key = f"{day}{str(h).zfill(2)}"
                        if start_dt <= datetime.datetime.strptime(dt_key, "%Y%m%d%H") <= end_dt:
                            for param in NASA_HOURLY_PARAMS.split(','):
                                hourly_results[param].append(np.nan)
        curr_dt += datetime.timedelta(days=1)
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
            print(f"    - Skipping row with invalid date components.", file=sys.stderr)
            return pd.Series({})
        start_dt = datetime.datetime(
            int(row['startyear']), int(row['startmonth']), int(row['startday']),
            int(s_time_str[:2]), int(s_time_str[2:])
        )
        lat = row['start_latitude']
        lng = row['start_longitude']
        if pd.isna(lat) or pd.isna(lng):
            print(f"    - Skipping row with invalid coordinates.", file=sys.stderr)
            return pd.Series({})

        # 정확히 24시간/12시간 구간의 각 날짜별로 끊어서 fetch!
        past_start_dt = start_dt - datetime.timedelta(hours=24)
        past_end_dt   = start_dt - datetime.timedelta(hours=1)
        past_hourly_values = fetch_nasa_hourly_timespan(lat, lng, past_start_dt, past_end_dt)
        future_start_dt = start_dt + datetime.timedelta(hours=1)
        future_end_dt   = start_dt + datetime.timedelta(hours=12)
        future_hourly_values = fetch_nasa_hourly_timespan(lat, lng, future_start_dt, future_end_dt)

        new_features = {}
        if past_hourly_values:
            for param, values in past_hourly_values.items():
                stats = create_trend_features(values)
                for stat_name, stat_value in stats.items():
                    new_features[f'{param.lower()}_{stat_name}_past_24h'] = stat_value
        if future_hourly_values:
            for param, values in future_hourly_values.items():
                stats = create_trend_features(values)
                for stat_name, stat_value in stats.items():
                    new_features[f'{param.lower()}_{stat_name}_forecast_12h'] = stat_value
        print(f"[DEBUG] {row['startyear']}-{row['startmonth']}-{row['startday']} NEW FEATURE 예시: {list(new_features.keys())[:3]} {list(new_features.values())[:3]}")
        return pd.Series(new_features)
    except Exception as e:
        print(f"    - Error processing row: {e}", file=sys.stderr)
        return pd.Series({})

# ... fetch_nasa_hourly_timespan, create_trend_features, enrich_fire_event 함수는 동일 ...

if __name__ == '__main__':
    print(f"Loading original dataset: '{INPUT_FILE}'...")
    try:
        df = pd.read_csv(INPUT_FILE, encoding='utf-8')
    except FileNotFoundError:
        print(f"FATAL: Input file not found at '{INPUT_FILE}'. Exiting.", file=sys.stderr)
        sys.exit(1)
    print(f"Loaded {len(df)} fire events. Starting enrichment process...")
    print("This will take a significant amount of time.")
    all_new_features = []
    total_rows = len(df)
    for index, row in df.iterrows():
        new_features = enrich_fire_event(row)
        all_new_features.append(new_features)
        if (index + 1) % 10 == 0:
            print(f"  - Processed {index + 1} / {total_rows} events...")
    new_features_df = pd.DataFrame(all_new_features, index=df.index)
    df_enriched = df.join(new_features_df)
    # --- Remove all old future-data columns ---
    future_weather_pattern = re.compile(r'_\d+h')
    cols_to_drop = []
    for col in df_enriched.columns:
        match = future_weather_pattern.search(col)
        if match and not col.endswith('_0h'):
            cols_to_drop.append(col)
        if 'end' in col or 'duration' in col:
            cols_to_drop.append(col)
    cols_to_drop.extend([col for col in df_enriched.columns if col.startswith('dt_')])
    df_final = df_enriched.drop(columns=cols_to_drop, errors='ignore')
    print(f"Removed {len(cols_to_drop)} old future-related columns.")
    try:
        df_final.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        print(f"✅ Successfully saved new enriched dataset to '{OUTPUT_FILE}'")
        print(f"Final dataset shape: {df_final.shape}")
    except Exception as e:
        print(f"\nFATAL: Error saving the final file: {e}", file=sys.stderr)



    # print(f"Loading original dataset: '{INPUT_FILE}'...")
    # try:
    #     df = pd.read_csv(INPUT_FILE, encoding='utf-8')
    # except FileNotFoundError:
    #     print(f"FATAL: Input file not found at '{INPUT_FILE}'. Exiting.", file=sys.stderr)
    #     sys.exit(1)
        
    # print(f"Loaded {len(df)} fire events. Starting enrichment process...")
    # print("This will take a significant amount of time.")

    # # 🔥 여기만 바꿔서 10개만 테스트!
    # N = 10
    # test_df = df.iloc[:N].copy()   # 10개만 슬라이싱

    # all_new_features = []
    # for index, row in test_df.iterrows():
    #     new_features = enrich_fire_event(row)
    #     all_new_features.append(new_features)
    #     print(f"  - Processed {index + 1} / {N} events...")

    # new_features_df = pd.DataFrame(all_new_features, index=test_df.index)
    # df_enriched = test_df.join(new_features_df)

    # # 저장 경로도 테스트용으로 바꿔주면 안전!
    # test_output_file = os.path.join(BASE_DIR, 'enriched_training_data_test10.csv')
    # df_enriched.to_csv(test_output_file, index=False, encoding='utf-8')
    # print(f"✅ [TEST] Saved 10-row sample to '{test_output_file}'")
    # print(f"Final dataset shape: {df_enriched.shape}")