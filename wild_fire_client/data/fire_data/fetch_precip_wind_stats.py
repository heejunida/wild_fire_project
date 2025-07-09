import pandas as pd
import requests
import datetime
import time

IN_CSV = "fire_weather_merged.csv"  # 너가 방금 업로드한 파일명
OUT_CSV = "fire_weather_merged_full.csv"
API_SLEEP = 2.0

# 10m 풍향/풍속 받아오는 함수
def fetch_nasa_hourly_10m(lat, lng, yyyymmdd, hour_str, max_retry=4):
    url = (
        f"https://power.larc.nasa.gov/api/temporal/hourly/point?"
        "parameters=WS10M,WD10M&community=RE"
        f"&longitude={lng}&latitude={lat}&start={yyyymmdd}&end={yyyymmdd}&format=JSON"
    )
    for attempt in range(max_retry):
        try:
            res = requests.get(url, timeout=30)
            res.raise_for_status()
            data = res.json().get("properties", {}).get("parameter", {})
            hour_key = f"{yyyymmdd}{hour_str.zfill(2)}"
            return {
                "WS10M": data.get("WS10M", {}).get(hour_key, ""),
                "WD10M": data.get("WD10M", {}).get(hour_key, "")
            }
        except Exception as e:
            print(f"[10m풍향/풍속 실패] {lat}, {lng}, {yyyymmdd} {hour_str}: {e}")
            time.sleep(3)
    return {"WS10M": "", "WD10M": ""}

# 누적강수, 무강수일수 함수
def fetch_nasa_daily_precip(lat, lng, start_date, end_date, max_retry=4):
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
            print(f"NASA 일별 강수량 API 실패 (시도 {attempt+1}/{max_retry}): {e}")
            time.sleep(3)
    return {}

df = pd.read_csv(IN_CSV, encoding="utf-8-sig")

# 결과 컬럼 초기화
periods = [7, 14, 30, 60, 90]
for p in periods:
    df[f"total_precip_{p}d"] = None
    df[f"no_rain_days_{p}d"] = None

df['WS10M'] = None
df['WD10M'] = None

for idx, row in df.iterrows():
    lat = row['lat']
    lng = row['lng']
    fire_date = datetime.datetime(int(row['startyear']), int(row['startmonth']), int(row['startday']))
    yyyymmdd = fire_date.strftime('%Y%m%d')
    hour = str(row['starttime']).split(":")[0] if pd.notnull(row['starttime']) else "12"
    
    # (1) 10m 풍향/풍속
    ws10m_wd10m = fetch_nasa_hourly_10m(lat, lng, yyyymmdd, hour)
    df.at[idx, 'WS10M'] = ws10m_wd10m['WS10M']
    df.at[idx, 'WD10M'] = ws10m_wd10m['WD10M']

    # (2) 누적강수/무강수일수
    for p in periods:
        end_date = (fire_date - datetime.timedelta(days=1)).strftime('%Y%m%d')   # 당일 제외
        start_date = (fire_date - datetime.timedelta(days=p)).strftime('%Y%m%d')
        precip_dict = fetch_nasa_daily_precip(lat, lng, start_date, end_date)
        precip_values = []
        for date in pd.date_range(start=start_date, end=end_date):
            val = precip_dict.get(date.strftime('%Y%m%d'), None)
            try:
                val = float(val) if val is not None else 0.0
            except:
                val = 0.0
            precip_values.append(val)
        total_precip = sum(precip_values)
        no_rain_days = sum(1 for v in precip_values if v < 0.1)
        df.at[idx, f"total_precip_{p}d"] = total_precip
        df.at[idx, f"no_rain_days_{p}d"] = no_rain_days

    print(f"[{idx+1}/{len(df)}] 처리 완료")
    time.sleep(API_SLEEP)

df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print(f"최종 저장 완료: {OUT_CSV}")