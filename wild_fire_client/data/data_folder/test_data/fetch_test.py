# data/fetch_test_fire_weather.py
import pandas as pd
import requests
import time

FIRE_CSV = "gangwon_fire_ml_input.csv"   # 실제 경로 확인!
OUT_CSV = "test_fire_weather_merged.csv"
API_SLEEP = 0.7

def fetch_nasa_hourly_weather(lat, lng, yyyymmdd, hour_str, max_retry=3):
    url = (
        f"https://power.larc.nasa.gov/api/temporal/hourly/point"
        f"?parameters=T2M,RH2M,WS2M,WD2M,PRECTOTCORR,PS,ALLSKY_SFC_SW_DWN"
        f"&community=RE&longitude={lng}&latitude={lat}"
        f"&start={yyyymmdd}&end={yyyymmdd}&format=JSON"
    )
    for attempt in range(max_retry):
        try:
            res = requests.get(url, timeout=20)
            res.raise_for_status()
            data = res.json().get("properties", {}).get("parameter", {})
            hour_key = f"{yyyymmdd}{hour_str.zfill(2)}"
            print("NASA 응답 OK")
            return {
                "T2M": data.get("T2M", {}).get(hour_key, ""),
                "RH2M": data.get("RH2M", {}).get(hour_key, ""),
                "WS2M": data.get("WS2M", {}).get(hour_key, ""),
                "WD2M": data.get("WD2M", {}).get(hour_key, ""),
                "PRECTOTCORR": data.get("PRECTOTCORR", {}).get(hour_key, ""),
                "PS": data.get("PS", {}).get(hour_key, ""),
                "ALLSKY_SFC_SW_DWN": data.get("ALLSKY_SFC_SW_DWN", {}).get(hour_key, "")
            }
        except Exception as e:
            print(f"NASA API 실패 (시도 {attempt+1}/{max_retry}): {e}")
            time.sleep(2.5)
    return None

# --- 1. 화재 데이터 읽기 (상위 10개만)
df = pd.read_csv(FIRE_CSV, encoding="utf-8-sig").head(10)

weather_cols = [
    "T2M", "RH2M", "WS2M", "WD2M",
    "PRECTOTCORR", "PS", "ALLSKY_SFC_SW_DWN"
]
final_cols = list(df.columns) + weather_cols

merged_rows = []

for idx, row in df.iterrows():
    lat = row['lat']
    lng = row['lng']
    yyyymmdd = f"{int(row['startyear']):04d}{int(row['startmonth']):02d}{int(row['startday']):02d}"
    hour = str(row['starttime']).split(":")[0] if pd.notnull(row['starttime']) else "12"

    print(f"[{idx+1}/10] {yyyymmdd} {hour}시 ({lat}, {lng}) → NASA 호출")
    weather = fetch_nasa_hourly_weather(lat, lng, yyyymmdd, hour)
    if weather is None:
        weather = {col:"" for col in weather_cols}
        print("⚠️ NASA 기상정보 없음 (공란 처리)")
    else:
        print("➡️ 병합 완료")

    merged_row = {**row, **weather}
    merged_rows.append(merged_row)
    time.sleep(API_SLEEP)

pd.DataFrame(merged_rows)[final_cols].to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print(f"\n🌱 테스트 10건 저장 완료: {OUT_CSV}")

# 저장된 파일을 미리 읽어보기
print(pd.read_csv(OUT_CSV, encoding="utf-8-sig").head())