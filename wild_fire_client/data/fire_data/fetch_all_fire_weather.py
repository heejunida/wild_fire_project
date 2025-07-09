import pandas as pd
import requests
import datetime
import time

FIRE_CSV = "gangwon_fire_ml_input.csv"
OUT_CSV = "fire_weather_merged_final.csv"
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

# 도우미 함수: HH:MM:SS → 시간(int)
def hour_from_timestr(timestr):
    if pd.isnull(timestr):
        return 12  # 결측값은 12시로
    try:
        return int(str(timestr).split(":")[0])
    except:
        return 12

# 1. 화재 데이터 읽기
df = pd.read_csv(FIRE_CSV, encoding="utf-8-sig")
result_rows = []
for idx, row in df.iterrows():
    lat = row['lat']
    lng = row['lng']
    # 날짜, 시간 추출
    start_dt = datetime.datetime(int(row['startyear']), int(row['startmonth']), int(row['startday']), hour_from_timestr(row['starttime']))
    end_dt = datetime.datetime(int(row['endyear']), int(row['endmonth']), int(row['endday']), hour_from_timestr(row['endtime']))
    duration = (end_dt - start_dt).total_seconds() / 3600  # 시간 단위

    # 포인트 추출 로직
    time_points = []
    if duration < 1.0:
        # 1시간 이하면 시작, 종료만
        time_points = [("start", start_dt), ("end", end_dt)]
    elif duration <= 4.0:
        # 1~4시간이면 시작, 중간, 종료
        mid_dt = start_dt + (end_dt - start_dt) / 2
        time_points = [("start", start_dt), ("mid", mid_dt), ("end", end_dt)]
    else:
        # 4시간 초과면 3시간 단위 + 종료
        time_points = []
        curr_dt = start_dt
        point_idx = 1
        while curr_dt < end_dt:
            time_points.append((f"pt{point_idx}", curr_dt))
            curr_dt += datetime.timedelta(hours=3)
            point_idx += 1
        # 종료시점이 마지막이 아니면 추가
        if (time_points[-1][1] != end_dt):
            time_points.append(("end", end_dt))

    # 각 포인트별로 기후값 뽑기
    row_data = row.to_dict()
    for tag, dt in time_points:
        yyyymmdd = dt.strftime("%Y%m%d")
        hour = dt.strftime("%H")
        weather = fetch_nasa_hourly_weather(lat, lng, yyyymmdd, hour)
        for k, v in weather.items():
            row_data[f"{k}_{tag}"] = v  # 예: T2M_start, T2M_mid, ...
        row_data[f"date_{tag}"] = yyyymmdd
        row_data[f"hour_{tag}"] = hour
        time.sleep(API_SLEEP)
    result_rows.append(row_data)
    print(f"[{idx+1}/{len(df)}] {row['fire_date']} 처리 완료 ({len(time_points)}개 포인트)")

# 최종 저장
pd.DataFrame(result_rows).to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print(f"\n최종 저장 완료: {OUT_CSV}")