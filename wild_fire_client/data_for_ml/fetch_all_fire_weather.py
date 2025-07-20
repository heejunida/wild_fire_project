import pandas as pd
import requests
import datetime
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

FIRE_CSV = "gangwon_fire_ml_input.csv"
OUT_CSV = "fire_weather_merged_final.csv"
API_SLEEP = 0.5
MAX_WORKERS = 7

# 전역 캐시
weather_cache = {}
precip_cache = {}

# NASA API (hourly weather)
def fetch_nasa_hourly_weather(lat, lng, yyyymmdd, hour_str, max_retry=3):
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
            res = requests.get(url, timeout=30)
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
            print(f"NASA API 실패 (시도 {attempt+1}/{max_retry}): {e}")
            time.sleep(3)
    weather_cache[cache_key] = {k: np.nan for k in ["T2M","RH2M","WS2M","WD2M","WS10M","WD10M","PRECTOTCORR","PS","ALLSKY_SFC_SW_DWN"]}
    return weather_cache[cache_key]

# 일별 강수량 가져오기 (최대 100일까지)
def fetch_nasa_daily_precip(lat, lng, start_date, end_date, max_retry=3):
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
            res = requests.get(url, timeout=30)
            res.raise_for_status()
            data = res.json().get("properties", {}).get("parameter", {}).get("PRECTOTCORR", {})
            # 날짜별 dict {yyyymmdd: 강수량}
            precip_cache[cache_key] = data
            return data
        except Exception as e:
            print(f"NASA 일별강수 API 실패 (시도 {attempt+1}/{max_retry}): {e}")
            time.sleep(3)
    precip_cache[cache_key] = {}
    return {}

def hour_from_timestr(timestr):
    if pd.isnull(timestr):
        return 12
    try:
        return int(str(timestr).split(":")[0])
    except:
        return 12

def make_time_points(start_dt, end_dt):
    points = [start_dt]  # start 반드시 포함
    curr_dt = start_dt
    while True:
        curr_dt += datetime.timedelta(hours=3)
        if curr_dt >= end_dt:
            break
        points.append(curr_dt)
    if points[-1] != end_dt:
        points.append(end_dt)  # end도 반드시 포함
    return points

# 강수 피처 구하기
def make_precip_features(lat, lng, dt, periods=[7,14,30,60,90]):
    res = {}
    dt_str = dt.strftime("%Y%m%d")
    for ndays in periods:
        sdate = (dt - datetime.timedelta(days=ndays-1)).strftime("%Y%m%d")
        precip_dict = fetch_nasa_daily_precip(lat, lng, sdate, dt_str)
        vals = [float(precip_dict.get((dt - datetime.timedelta(days=i)).strftime("%Y%m%d"), np.nan)) for i in range(ndays)][::-1]
        arr = np.array(vals, dtype=float)
        # 누적강수량
        res[f"total_precip_{ndays}d"] = np.nansum(arr)
        # 무강수일수(1mm 미만)
        res[f"dry_days_{ndays}d"] = np.sum(arr < 1)
    # 연속 무강수일수(최근부터 몇일째 비 안옴, 1mm 미만)
    cons = 0
    for v in arr[::-1]:
        if np.isnan(v) or v < 1:
            cons += 1
        else:
            break
    res[f"consecutive_dry_days"] = cons
    return res

def single_fire_weather_job(fire_row, idx):
    lat = fire_row['lat']
    lng = fire_row['lng']
    start_dt = datetime.datetime(int(fire_row['startyear']), int(fire_row['startmonth']), int(fire_row['startday']), hour_from_timestr(fire_row['starttime']))
    end_dt = datetime.datetime(int(fire_row['endyear']), int(fire_row['endmonth']), int(fire_row['endday']), hour_from_timestr(fire_row['endtime']))
    duration = (end_dt - start_dt).total_seconds() / 3600

    time_points = make_time_points(start_dt, end_dt)
    time_tags = [f"{int((dt-start_dt).total_seconds()//3600)}h" if i!=len(time_points)-1 else "end"
                 for i, dt in enumerate(time_points)]
    
    row_data = fire_row.to_dict()

    # --- start 기준 누적강수/무강수일만 계산 ---
    precip_feats = make_precip_features(lat, lng, start_dt)
    for k, v in precip_feats.items():
        row_data[f"{k}_start"] = v

    # --- 각 시점별 기후 + datetime만 ---
    for tag, dt in zip(time_tags, time_points):
        yyyymmdd = dt.strftime("%Y%m%d")
        hour = dt.strftime("%H")
        weather = fetch_nasa_hourly_weather(lat, lng, yyyymmdd, hour)
        for k, v in weather.items():
            try:
                row_data[f"{k}_{tag}"] = float(v)
            except:
                row_data[f"{k}_{tag}"] = np.nan
        row_data[f"dt_{tag}"] = dt.strftime("%Y-%m-%d %H:%M")
        time.sleep(API_SLEEP)
    row_data["fire_duration_hours"] = duration
    return row_data

if __name__ == "__main__":
    df = pd.read_csv(FIRE_CSV, encoding="utf-8-sig")
    result_rows = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(single_fire_weather_job, row, idx) for idx, row in df.iterrows()]
        for i, f in enumerate(as_completed(futures)):
            try:
                res = f.result()
                result_rows.append(res)
                print(f"[{i+1}/{len(df)}] 처리 완료: {res.get('fire_date', '')}")
            except Exception as e:
                print(f"[Error] {i+1}번째 row 실패: {e}")

    pd.DataFrame(result_rows).to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n최종 저장 완료: {OUT_CSV}")