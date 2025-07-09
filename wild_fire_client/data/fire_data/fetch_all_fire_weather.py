import pandas as pd
import requests
import datetime
import time

FIRE_CSV = "gangwon_fire_ml_input.csv"   # 반드시 경로 확인!
OUT_CSV = "fire_weather_merged.csv"
API_SLEEP = 2.0   # 네트워크 상황 맞게 충분히 여유!

def fetch_nasa_hourly_weather(lat, lng, yyyymmdd, hour_str, max_retry=4):
    url = (
        f"https://power.larc.nasa.gov/api/temporal/hourly/point?"
        "parameters=T2M,RH2M,WS2M,WD2M,PRECTOTCORR,PS,ALLSKY_SFC_SW_DWN"
        f"&community=RE&longitude={lng}&latitude={lat}&start={yyyymmdd}&end={yyyymmdd}&format=JSON"
    )
    for attempt in range(max_retry):
        try:
            res = requests.get(url, timeout=30)
            res.raise_for_status()
            data = res.json().get("properties", {}).get("parameter", {})
            hour_key = f"{yyyymmdd}{hour_str.zfill(2)}"
            print("NASA API 호출 성공:", lat, lng, yyyymmdd, hour_str)
            return {
                "T2M": data.get("T2M", {}).get(hour_key, ""),
                "RH2M": data.get("RH2M", {}).get(hour_key, ""),
                "WS2M": data.get("WS2M", {}).get(hour_key, ""),
                "WD2M": data.get("WD2M", {}).get(hour_key, ""),
                "PRECTOTCORR": data.get("PRECTOTCORR", {}).get(hour_key, ""),  # 강수량 (mm)
                "PS": data.get("PS", {}).get(hour_key, ""),
                "ALLSKY_SFC_SW_DWN": data.get("ALLSKY_SFC_SW_DWN", {}).get(hour_key, "")
            }
        except Exception as e:
            print(f"NASA API 실패 (시도 {attempt+1}/{max_retry}): {e}")
            time.sleep(3)  # 재시도 전 쉬기
    return {  # 실패시 빈 값
        "T2M": "", "RH2M": "", "WS2M": "", "WD2M": "",
        "PRECTOTCORR": "", "PS": "", "ALLSKY_SFC_SW_DWN": ""
    }

# 1. 화재 데이터 읽기
df = pd.read_csv(FIRE_CSV, encoding="utf-8-sig")

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

    print(f"[{idx+1}/{len(df)}] {yyyymmdd} {hour}시 ({lat}, {lng}) → NASA 호출")
    weather = fetch_nasa_hourly_weather(lat, lng, yyyymmdd, hour)
    merged_row = {**row, **weather}
    merged_rows.append(merged_row)

    time.sleep(API_SLEEP)

pd.DataFrame(merged_rows)[final_cols].to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print(f"\n최종 저장 완료: {OUT_CSV}")