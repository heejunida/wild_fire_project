import pandas as pd
import numpy as np
from datetime import timedelta
import requests
import time

CSV_FILE = 'preprocess/csv/datetime_changed_end.csv'
OUT_CSV = 'fire_weather_timeslot_FIXED_with_datetime_cols.csv'
VAR_KEYS = [
    'T2M', 'RH2M', 'WS2M', 'WD2M',
    'PRECTOTCORR', 'PS', 'ALLSKY_SFC_SW_DWN',
    'WS10M', 'WD10M'
]

def fetch_nasa_day_weather(lat, lng, yyyymmdd, max_retries=3, delay=5):
    url = (
        f"https://power.larc.nasa.gov/api/temporal/hourly/point?"
        f"parameters={','.join(VAR_KEYS)}"
        f"&community=RE&longitude={lng}&latitude={lat}&start={yyyymmdd}&end={yyyymmdd}&format=JSON"
    )
    for attempt in range(max_retries):
        try:
            res = requests.get(url, timeout=45)
            res.raise_for_status()
            return res.json().get("properties", {}).get("parameter", {})
        except Exception as e:
            print(f"NASA API ERROR (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                print(f"재시도 {delay}초 후 진행...")
                time.sleep(delay)
            else:
                print("최대 재시도 횟수 도달, 넘어갑니다.")
    return {k: {} for k in VAR_KEYS}

def get_hourly_weather(data, dt):
    yyyymmdd = dt.strftime('%Y%m%d')
    hour_str = dt.strftime('%H').zfill(2)
    hour_key = f"{yyyymmdd}{hour_str}"
    return {k: data.get(k, {}).get(hour_key, np.nan) for k in VAR_KEYS}

def dt_str_to_obj(dtstr):
    return pd.to_datetime(dtstr, errors='coerce')

def safe_ymd(val):
    if pd.isnull(val) or str(val).strip() in ['', 'nan', 'NaN', '0.0', '0', '00']:
        return ''
    try:
        return str(int(float(val)))
    except Exception:
        sval = str(val)
        if '.' in sval:
            return sval.split('.')[0]
        return sval

def safe_hour(val):
    if pd.isnull(val) or str(val).strip() in ['', 'nan', 'NaN', '0.0']:
        return ''
    try:
        return str(int(float(val))).zfill(2)
    except Exception:
        sval = str(val)
        if '.' in sval:
            sval = sval.split('.')[0]
        return sval.zfill(2)

def values_differ(a, b, tol=1e-6):
    if pd.isnull(a) and pd.isnull(b):
        return False
    if pd.isnull(a) != pd.isnull(b):
        return True
    try:
        a_f = float(a)
        b_f = float(b)
        return abs(a_f - b_f) > tol
    except:
        return str(a) != str(b)

# --- CSV 읽을 때 date/hour 문자형 강제
tmp_cols = pd.read_csv(CSV_FILE, nrows=1).columns
date_cols = [c for c in tmp_cols if c.startswith('date_')]
hour_cols = [c for c in tmp_cols if c.startswith('hour_')]
str_dtype = {c: str for c in (date_cols + hour_cols)}
df = pd.read_csv(CSV_FILE, dtype=str_dtype)
df_new = df.copy()

for idx, row in df.iterrows():
    lat, lng = row['lat'], row['lng']
    start_dt = dt_str_to_obj(row['start_datetime'])
    end_dt = dt_str_to_obj(row['end_datetime'])
    if pd.isnull(start_dt) or pd.isnull(end_dt):
        continue
    duration_hours = (end_dt - start_dt).total_seconds() / 3600

    check_points = {}
    # 2시간 이하: start, end (1시간 -> 2시간으로 변경)
    if duration_hours < 2:
        check_points['start'] = start_dt
        if start_dt != end_dt:
            check_points['end'] = end_dt
    # 2~4시간: start, mid, end
    elif duration_hours <= 4:
        check_points['start'] = start_dt
        mid_dt = start_dt + (end_dt - start_dt) / 2
        check_points['mid'] = mid_dt
        check_points['end'] = end_dt
    # 4시간 초과: start, pt1, pt2, ..., end (3시간 단위)
    else:
        check_points['start'] = start_dt
        pt_idx = 1
        while True:
            pt_dt = start_dt + timedelta(hours=3 * pt_idx)
            if pt_dt >= end_dt:
                break
            check_points[f'pt{pt_idx}'] = pt_dt
            pt_idx += 1
        check_points['end'] = end_dt

    need_dates = set([dt.strftime('%Y%m%d') for dt in check_points.values()])
    nasa_weather = {d: fetch_nasa_day_weather(lat, lng, d) for d in need_dates}

    # start 날짜/시간과 기후 데이터 로그 출력 (추가)
    start_ymd = start_dt.strftime('%Y%m%d')
    start_h = start_dt.strftime('%H').zfill(2)
    start_weather = get_hourly_weather(nasa_weather[start_ymd], start_dt)
    print(f"[{idx}] start (날짜/시간: {start_ymd} {start_h}) NASA 기후 데이터: " + ", ".join(f"{v}={start_weather[v]}" for v in VAR_KEYS))

    for key, dt in check_points.items():
        ymd = dt.strftime('%Y%m%d')
        h = dt.strftime('%H').zfill(2)

        old_ymd = safe_ymd(row.get(f'date_{key}', ''))
        old_h = safe_hour(row.get(f'hour_{key}', ''))

        if old_ymd == '' or old_h == '':
            if key == 'start':
                dt_ref = start_dt
            elif key == 'end':
                dt_ref = end_dt
            elif key == 'mid':
                dt_ref = start_dt + (end_dt - start_dt) / 2
            else:
                dt_ref = check_points.get(key, None)
            if dt_ref is not None:
                old_ymd = dt_ref.strftime('%Y%m%d')
                old_h = dt_ref.strftime('%H').zfill(2)

        nasa_vals = get_hourly_weather(nasa_weather[ymd], dt)

        if key != 'start':
            print(f"[{idx}] {key} (날짜/시간: {ymd} {h}) NASA 기후 데이터: " + ", ".join(f"{v}={nasa_vals[v]}" for v in VAR_KEYS))

        needs_update = False
        if (old_ymd != ymd) or (old_h != h):
            needs_update = True
        else:
            for v in VAR_KEYS:
                csv_val = row.get(f"{v}_{key}", np.nan)
                nasa_val = nasa_vals[v]
                if not values_differ(csv_val, nasa_val):
                    continue
                needs_update = True
                break

        if needs_update:
            prev_vals_str = ", ".join(f"{v}={row.get(f'{v}_{key}', '(없음)')}" for v in VAR_KEYS)
            nasa_vals_str = ", ".join(f"{v}={nasa_vals[v]}" for v in VAR_KEYS)

            print(f"[{idx}] {key} (날짜/시간:{old_ymd or '(빈)'} {old_h or '(빈)'} → {ymd} {h}) 값 불일치, NASA 값으로 덮어씀")
            print(f"    이전 CSV 기후 데이터: {prev_vals_str}")
            print(f"    NASA 기후 데이터: {nasa_vals_str}")

            df_new.at[idx, f'date_{key}'] = str(ymd)
            df_new.at[idx, f'hour_{key}'] = str(h).zfill(2)
            for v in VAR_KEYS:
                df_new.at[idx, f"{v}_{key}"] = nasa_vals[v]

        if key == 'mid':
            df_new.at[idx, 'mid_datetime'] = dt.strftime('%Y-%m-%d %H:%M:%S')
        elif key.startswith('pt'):
            df_new.at[idx, f'{key}_datetime'] = dt.strftime('%Y-%m-%d %H:%M:%S')

# 날짜/시간 컬럼 문자형 캐스팅
str_cols = [c for c in df_new.columns if c.startswith('date_') or c.startswith('hour_')]
df_new[str_cols] = df_new[str_cols].astype(str)

mid_cols = [c for c in df_new.columns if '_mid' in c] + ['mid_datetime', 'date_mid', 'hour_mid']

for idx, row in df_new.iterrows():
    start_dt = dt_str_to_obj(row['start_datetime'])
    end_dt = dt_str_to_obj(row['end_datetime'])
    if pd.isnull(start_dt) or pd.isnull(end_dt):
        continue
    duration_hours = (end_dt - start_dt).total_seconds() / 3600
    if duration_hours > 4:
        for col in mid_cols:
            if col in df_new.columns:
                df_new.at[idx, col] = np.nan

df_new.to_csv(OUT_CSV, index=False, encoding='utf-8-sig')
print(f"\n최종 저장 완료: {OUT_CSV}")