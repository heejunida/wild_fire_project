import pandas as pd
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

IN_CSV = "fire_weather_merged_final_with_filled_all_fixed.csv"
OUT_CSV = "fire_weather_merged_full_final_real.csv"
OUT_XLSX = "fire_weather_merged_full_final_real.xlsx"
API_SLEEP = 1.0  # 병렬화라서 1.0 정도로 시작 (0.5도 테스트 가능)
MAX_WORKERS = 4  # 동시에 몇 개까지 병렬 요청할지 (NASA block 방지: 3~6 추천)

# --- 1. API 함수 ---
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

# --- 2. 파일 로드 ---
df = pd.read_csv(IN_CSV, encoding="utf-8-sig")

# --- 3. 누적강수량/무강수일수 (start 기준) 컬럼 초기화 ---
periods = [7, 14, 30, 60, 90]
new_cols_precip = {f"total_precip_{p}d": None for p in periods}
new_cols_precip.update({f"no_rain_days_{p}d": None for p in periods})

# --- 4. 풍향/풍속 컬럼 초기화 (start, end, mid, pt*) ---
weather_points = []
for col in df.columns:
    if col.startswith("date_"):
        tag = col.replace("date_", "")
        weather_points.append(tag)
weather_points = sorted(set(weather_points))  # ex) ['end', 'mid', 'pt1', ... , 'start']

new_cols_wind = {f'WS10M_{tag}': None for tag in weather_points}
new_cols_wind.update({f'WD10M_{tag}': None for tag in weather_points})

# --- 5. 한번에 컬럼 붙이기 (fragmentation 방지) ---
df = pd.concat([df, pd.DataFrame([new_cols_precip | new_cols_wind] * len(df), index=df.index)], axis=1)

# --- 6. 풍향/풍속 병렬 작업 준비 ---
wind_tasks = []
for idx, row in df.iterrows():
    lat = row['lat']
    lng = row['lng']
    for tag in weather_points:
        date_col = f"date_{tag}"
        hour_col = f"hour_{tag}"
        if pd.isnull(row.get(date_col)) or pd.isnull(row.get(hour_col)):
            continue
        yyyymmdd = str(row[date_col]).replace(".0","").zfill(8)
        hour = str(row[hour_col]).replace(".0","").zfill(2)
        # 이미 값이 있으면 skip
        if not (pd.isnull(row.get(f"WS10M_{tag}")) or row.get(f"WS10M_{tag}") == ""):
            continue
        wind_tasks.append((idx, tag, lat, lng, yyyymmdd, hour))

# --- 7. 풍향/풍속 병렬 처리 ---
def wind_worker(task):
    idx, tag, lat, lng, yyyymmdd, hour = task
    ws10m_wd10m = fetch_nasa_hourly_10m(lat, lng, yyyymmdd, hour)
    return (idx, tag, ws10m_wd10m)

print(f"풍향/풍속 병렬 요청 준비: 총 {len(wind_tasks)}개")
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(wind_worker, task) for task in wind_tasks]
    for i, future in enumerate(as_completed(futures), 1):
        idx, tag, ws10m_wd10m = future.result()
        df.at[idx, f'WS10M_{tag}'] = ws10m_wd10m['WS10M']
        df.at[idx, f'WD10M_{tag}'] = ws10m_wd10m['WD10M']
        print(f"[{i}/{len(wind_tasks)}] {tag} 풍향/풍속 완료: {df.at[idx, 'fire_date']} {tag} ({df.at[idx, 'lat']},{df.at[idx, 'lng']})")
        time.sleep(API_SLEEP)  # NASA block 피하기 위해 병렬이라도 sleep은 남겨둠

# --- 8. 누적강수/무강수일수 (start 기준) - 병렬화 안함(1개만 요청, block 위험)
for idx, row in df.iterrows():
    lat = row['lat']
    lng = row['lng']
    fire_date = None
    try:
        fire_date = pd.to_datetime(f"{int(row['startyear'])}-{int(row['startmonth']):02}-{int(row['startday']):02}")
    except:
        continue
    for p in periods:
        end_date = (fire_date - pd.Timedelta(days=1)).strftime('%Y%m%d')   # start 당일 제외
        start_date = (fire_date - pd.Timedelta(days=p)).strftime('%Y%m%d')
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
    print(f"[{idx+1}/{len(df)}] 강수/무강수일수 완료")
    time.sleep(API_SLEEP)

# --- 9. 저장 ---
df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print(f"\n최종 저장 완료: {OUT_CSV}")

df.to_excel(OUT_XLSX, index=False)
print(f"엑셀 파일도 저장 완료: {OUT_XLSX}")