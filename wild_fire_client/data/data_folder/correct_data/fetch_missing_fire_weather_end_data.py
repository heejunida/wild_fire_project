import pandas as pd
import requests
import time

FIRE_CSV = "fire_weather_merged_final_with_filled_start_fixed.csv"
OUT_CSV = "fire_weather_merged_final_with_filled_start_end_fixed.csv"
OUT_XLSX = "fire_weather_merged_final_with_filled_start_end_fixed.xlsx"
API_SLEEP = 2.0

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
            time.sleep(3)
    return {
        "T2M": "", "RH2M": "", "WS2M": "", "WD2M": "",
        "PRECTOTCORR": "", "PS": "", "ALLSKY_SFC_SW_DWN": ""
    }

def hour_from_timestr(timestr):
    if pd.isnull(timestr):
        return "12"
    try:
        return str(int(str(timestr).split(":")[0])).zfill(2)
    except:
        return "12"

# 1. CSV 읽기
df = pd.read_csv(FIRE_CSV, encoding="utf-8-sig")

# 🔑 date_end, hour_end 컬럼을 미리 문자열로 변환 (없으면 무시)
for col in ["date_end", "hour_end"]:
    if col in df.columns:
        df[col] = df[col].astype(str)

# 2. end 기후 데이터 비어있는 행만 찾아서 보완
for idx, row in df.iterrows():
    # 이미 값 있으면 skip
    if not (pd.isnull(row.get("T2M_end")) or row.get("T2M_end") == "" or str(row.get("T2M_end")).lower() == "nan"):
        continue

    lat = row["lat"]
    lng = row["lng"]
    yyyymmdd = f"{int(row['endyear']):04}{int(row['endmonth']):02}{int(row['endday']):02}"
    hour = hour_from_timestr(row["endtime"])

    print(f"[{idx+1}/{len(df)}] end값 보완: {yyyymmdd} {hour}시 ({lat},{lng})")

    weather = fetch_nasa_hourly_weather(lat, lng, yyyymmdd, hour)
    for k, v in weather.items():
        df.at[idx, f"{k}_end"] = v
    # 여기를 문자열로!
    df.at[idx, "date_end"] = str(yyyymmdd)
    df.at[idx, "hour_end"] = str(hour)
    time.sleep(API_SLEEP)

# 3. 저장
df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print(f"\n최종 저장 완료: {OUT_CSV}")
df.to_excel(OUT_XLSX, index=False)
print(f"엑셀 파일도 저장 완료: {OUT_XLSX}")