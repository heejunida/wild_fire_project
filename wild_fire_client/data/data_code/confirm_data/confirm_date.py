import pandas as pd

CSV_IN = 'fire_weather_timeslot_FIXED_with_datetime_cols.csv'
CSV_OUT = 'fire_weather_timeslot_FIXED_with_datetime_cols_datetimeonly.csv'

# 파일 읽기
df = pd.read_csv(CSV_IN, dtype=str)

# 삭제할 컬럼 리스트 만들기: date_*, hour_* (단, *_datetime은 남김)
drop_cols = [col for col in df.columns 
             if (col.startswith('date_') or col.startswith('hour_')) and not col.endswith('_datetime')]

# 컬럼 삭제
df.drop(columns=drop_cols, inplace=True)

# 저장
df.to_csv(CSV_OUT, index=False, encoding='utf-8-sig')

print(f"삭제된 컬럼: {drop_cols}")
print(f"최종 저장: {CSV_OUT}")