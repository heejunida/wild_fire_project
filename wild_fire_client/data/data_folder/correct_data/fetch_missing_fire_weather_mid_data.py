import pandas as pd
import requests
import datetime
import time

FIRE_CSV = "fire_weather_merged_final_with_filled_start_end_fixed.csv"
OUT_CSV = "fire_weather_merged_final_with_filled_all_fixed.csv"
OUT_XLSX = "fire_weather_merged_final_with_filled_all_fixed.xlsx"
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
    return {  # 실패시 빈 값
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

# 컬럼 타입 명시적 변환 (object=문자열)
df["date_mid"] = df["date_mid"].astype(str)
df["hour_mid"] = df["hour_mid"].astype(str)

# 2. mid 결측 row만 보정
for idx, row in df.iterrows():
    # duration 계산
    try:
        start_dt = datetime.datetime(int(row['startyear']), int(row['startmonth']), int(row['startday']),
                                     int(str(row['starttime']).split(":")[0]))
        end_dt = datetime.datetime(int(row['endyear']), int(row['endmonth']), int(row['endday']),
                                   int(str(row['endtime']).split(":")[0]))
        duration = (end_dt - start_dt).total_seconds() / 3600
    except:
        continue

    # 조건: 1~4시간 구간이면서 mid 값이 비어있는 경우만
    if (1.0 <= duration <= 4.0) and (pd.isnull(row.get("T2M_mid")) or row.get("T2M_mid") == ""):
        lat = row["lat"]
        lng = row["lng"]
        # start와 end의 중간 시각 구하기
        mid_dt = start_dt + (end_dt - start_dt) / 2
        yyyymmdd = mid_dt.strftime("%Y%m%d")
        hour = mid_dt.strftime("%H")
        print(f"[{idx+1}/{len(df)}] mid값 보완: {yyyymmdd} {hour}시 ({lat},{lng})")

        weather = fetch_nasa_hourly_weather(lat, lng, yyyymmdd, hour)
        for k, v in weather.items():
            df.at[idx, f"{k}_mid"] = v
        df.at[idx, "date_mid"] = str(yyyymmdd)
        df.at[idx, "hour_mid"] = str(hour)
        time.sleep(API_SLEEP)

# 3. 저장
df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print(f"\n최종 저장 완료: {OUT_CSV}")
df.to_excel(OUT_XLSX, index=False)
print(f"엑셀 파일도 저장 완료: {OUT_XLSX}")