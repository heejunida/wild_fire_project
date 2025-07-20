import requests
import datetime
import sys
import json
import numpy as np
import traceback

def fetch_nasa_hourly_weather(lat, lng, yyyymmdd, hour_str, max_retry=3):
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
            return result
        except Exception as e:
            if attempt == max_retry-1:
                raise e

def fetch_nasa_daily_precip(lat, lng, start_date, end_date, max_retry=3):
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
            return data
        except Exception as e:
            if attempt == max_retry-1:
                raise e

def make_precip_features(lat, lng, end_dt, periods=[7,14,30,60,90]):
    res = {}
    dt_str = end_dt.strftime("%Y%m%d")
    for ndays in periods:
        sdate = (end_dt - datetime.timedelta(days=ndays-1)).strftime("%Y%m%d")
        precip_dict = fetch_nasa_daily_precip(lat, lng, sdate, dt_str)
        vals = [float(precip_dict.get((end_dt - datetime.timedelta(days=i)).strftime("%Y%m%d"), np.nan)) for i in range(ndays)][::-1]
        arr = np.array(vals, dtype=float)
        res[f"total_precip_{ndays}d"] = np.nansum(arr)
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

def make_time_points(start_dt, end_dt, interval_hours=3):
    points = [start_dt]
    curr_dt = start_dt
    while True:
        curr_dt += datetime.timedelta(hours=interval_hours)
        if curr_dt >= end_dt:
            break
        points.append(curr_dt)
    if points[-1] != end_dt:
        points.append(end_dt)
    return points

if __name__ == "__main__":
    try:
        lat = float(sys.argv[1])
        lng = float(sys.argv[2])
        start_yyyymmdd = sys.argv[3]
        start_hhmm = sys.argv[4]
        end_yyyymmdd = sys.argv[5]
        end_hhmm = sys.argv[6]
        start_dt = datetime.datetime.strptime(start_yyyymmdd + start_hhmm, "%Y%m%d%H%M")
        end_dt = datetime.datetime.strptime(end_yyyymmdd + end_hhmm, "%Y%m%d%H%M")
        # duration = (end_dt - start_dt).total_seconds() / 3600
    except Exception:
        print(json.dumps({
            "success": False,
            "error": "인자 부족! 사용법: python fetch_weather_data.py lat lng start_yyyymmdd start_hhmm end_yyyymmdd end_hhmm"
        }, ensure_ascii=False))
        sys.exit(2)

    try:
        # 구간 전체 누적강수, 무강수 피처 (end 기준)
        precip = make_precip_features(lat, lng, end_dt)

        # 3시간 단위(최대 12시간 → 5개 시점) 시계열 기후 데이터
        time_points = make_time_points(start_dt, end_dt, interval_hours=3)
        weather_list = []
        for dt in time_points:
            yyyymmdd = dt.strftime("%Y%m%d")
            hour_str = dt.strftime("%H")
            w = fetch_nasa_hourly_weather(lat, lng, yyyymmdd, hour_str)
            weather_list.append({
                "dt": dt.strftime("%Y-%m-%d %H:%M"),
                **w
            })

        # 평균, 최대, 최소값 등 요약 feature
        summary_feats = {}
        for var in ["T2M","RH2M","WS2M","WD2M","WS10M","WD10M","PRECTOTCORR","PS","ALLSKY_SFC_SW_DWN"]:
            arr = np.array([x[var] for x in weather_list if var in x and x[var] is not None], dtype=float)
            summary_feats[f"{var}_mean"] = float(np.nanmean(arr)) if arr.size else None
            summary_feats[f"{var}_max"] = float(np.nanmax(arr)) if arr.size else None
            summary_feats[f"{var}_min"] = float(np.nanmin(arr)) if arr.size else None

        result = {
            "lat": lat,
            "lng": lng,
            "start_dt": start_dt.strftime("%Y-%m-%d %H:%M"),
            "end_dt": end_dt.strftime("%Y-%m-%d %H:%M"),
            "duration_hours": round((end_dt-start_dt).total_seconds()/3600,2),
            "weather_timeseries": weather_list,   # 3시간 단위 값 전체 (최대 5개 시점)
            **precip,
            **summary_feats,
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