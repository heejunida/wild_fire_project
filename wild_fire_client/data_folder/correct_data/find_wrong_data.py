import pandas as pd

# 파일명에 맞게 수정
DATA_CSV = "fire_weather_merged_final_with_filled_all_fixed.csv"

# 1. 데이터 불러오기
df = pd.read_csv(DATA_CSV, encoding="utf-8-sig")

# 2. duration(화재 지속 시간) 계산
def calc_duration(row):
    try:
        from datetime import datetime
        start_dt = datetime(
            int(row['startyear']), int(row['startmonth']), int(row['startday']),
            int(str(row['starttime']).split(":")[0])
        )
        end_dt = datetime(
            int(row['endyear']), int(row['endmonth']), int(row['endday']),
            int(str(row['endtime']).split(":")[0])
        )
        return (end_dt - start_dt).total_seconds() / 3600
    except Exception:
        return None

df['duration_hr'] = df.apply(calc_duration, axis=1)

# 3. 각 구간별 row 수
total_rows = len(df)
duration_lt_1 = (df['duration_hr'] < 1).sum()
duration_1_to_4 = ((df['duration_hr'] >= 1) & (df['duration_hr'] <= 4)).sum()
duration_gt_4 = (df['duration_hr'] > 4).sum()

# 4. 컬럼별 결측 row 수
def is_null_or_empty(val):
    return pd.isnull(val) or val == ''

start_null = df['T2M_start'].apply(is_null_or_empty).sum()
mid_null = df['T2M_mid'].apply(is_null_or_empty).sum() if 'T2M_mid' in df.columns else 0
end_null = df['T2M_end'].apply(is_null_or_empty).sum()

print({
    "total_rows": total_rows,
    "duration_lt_1": duration_lt_1,
    "duration_1_to_4": duration_1_to_4,
    "duration_gt_4": duration_gt_4,
    "start_null": start_null,
    "mid_null": mid_null,
    "end_null": end_null
})

# 5. (선택) 1~4시간 구간인데 mid 결측 row 샘플 뽑기
df_1_4hr = df[(df['duration_hr'] >= 1) & (df['duration_hr'] <= 4)]
mid_null_in_1_4 = df_1_4hr[df_1_4hr['T2M_mid'].apply(is_null_or_empty)]
print(f"1~4시간인데 mid가 빈 row 수: {len(mid_null_in_1_4)}")
if len(mid_null_in_1_4) > 0:
    print(mid_null_in_1_4[['fire_date', 'starttime', 'endtime', 'duration_hr']].head())