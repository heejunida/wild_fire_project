import pandas as pd
import requests

def get_nasa_power_weather(lat, lon, year, month, day, hour):
    date_str = f"{year}{month:02d}{day:02d}"
    parameters = 'T2M,RH2M,WS2M,WS10M,WD2M,WD10M,PRECTOTCORR,PS,ALLSKY_SFC_SW_DWN'
    url = (
        f"https://power.larc.nasa.gov/api/temporal/hourly/point"
        f"?start={date_str}&end={date_str}"
        f"&latitude={lat}&longitude={lon}"
        f"&community=AG"
        f"&parameters={parameters}"
        f"&format=JSON"
        f"&user=example"
    )
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"NASA POWER API 오류: status={resp.status_code}")
        return None
    try:
        params = resp.json()["properties"]["parameter"]
        key = f"{date_str}{hour:02d}"
        return {var: params[var][key] if key in params[var] else None for var in params}
    except Exception as e:
        print("파싱 에러:", e)
        return None

# 1. 두 파일 불러오기
df1 = pd.read_csv("preprocess/csv/final_data_with_features_with_correct_duration_time.csv")
df2 = pd.read_csv("first_final_data.csv")

# 2. end date(연/월/일)만 비교해서 다른 row 찾기
end_cols_file1 = ['end_year', 'end_month', 'end_day']
end_cols_file2 = ['endyear', 'endmonth', 'endday']
min_len = min(len(df1), len(df2))

mismatch_rows = []
for idx in range(min_len):
    v1 = tuple(df1.loc[idx, end_cols_file1])
    v2 = tuple(df2.loc[idx, end_cols_file2])
    if v1 != v2:
        mismatch_rows.append(idx)

print(f"총 {len(mismatch_rows)}개의 row에서 end date(연/월/일)가 다름.\n")

# 3. NASA POWER API로 end date, time 기후데이터 받아오기
weather_results = []
for i, idx in enumerate(mismatch_rows, 1):
    row1 = df1.loc[idx]  # 날짜(정확한) 정보
    row2 = df2.loc[idx]  # 위치(lat/lng) 등 정보
    try:
        lat, lng = float(row2['lat']), float(row2['lng'])
        year, month, day, hour = int(row1['end_year']), int(row1['end_month']), int(row1['end_day']), int(row1['end_hour'])
        print(f"[{i}] row={idx} 위경도=({lat}, {lng}), 날짜={year}-{month}-{day} {hour}:00")
        weather = get_nasa_power_weather(lat, lng, year, month, day, hour)
        if weather is not None:
            print(f"  -> 기후데이터 OK: {weather}")
            result = {
                "row_idx": idx, "lat": lat, "lng": lng, "year": year, "month": month, "day": day, "hour": hour, **weather
            }
            weather_results.append(result)
        else:
            print("  -> NASA 데이터 수집 실패.")
    except Exception as e:
        print(f"  -> 에러: {e}")

# 4. 결과 저장
weather_df = pd.DataFrame(weather_results)
weather_df.to_csv("end_datetime_nasapower_weather.csv", index=False)
print("\n✔️ end date+time 기준 NASA 기후데이터 저장 완료: end_datetime_nasapower_weather.csv")