import pandas as pd

# 파일 읽기
df = pd.read_csv('fire_weather_timeslot_FIXED_with_datetime_cols.csv')

# mid와 ptN(datetime) 컬럼 찾기
mid_cols = [c for c in df.columns if '_mid' in c] + ['mid_datetime', 'date_mid', 'hour_mid']
pt_cols = [c for c in df.columns if '_pt' in c and 'datetime' in c] + \
          [c for c in df.columns if c.startswith('date_pt')] + \
          [c for c in df.columns if c.startswith('hour_pt')]

# mid가 있는 row만 추출 (datetime 기준, 빈값/NaN은 제외)
df_mid = df[df['mid_datetime'].notnull() & (df['mid_datetime'] != '')]

# ptN(datetime) 컬럼 중 하나라도 값이 있는 row 찾기
def has_pt_val(row):
    for ptcol in [c for c in df.columns if 'pt' in c and 'datetime' in c]:
        v = row.get(ptcol, None)
        if pd.notnull(v) and str(v).strip() != '':
            return True
    return False

# mid와 ptN 모두 값이 있는 row만 필터
df_mid_pt = df_mid[df_mid.apply(has_pt_val, axis=1)]

# 결과 출력 (몇 개만)
print(f"mid와 ptN이 모두 값이 있는 row 개수: {len(df_mid_pt)}")
print(df_mid_pt[['start_datetime', 'end_datetime', 'mid_datetime'] + [c for c in df_mid_pt.columns if 'pt' in c and 'datetime' in c]].head())
print(df_mid_pt[[col for col in df_mid_pt.columns if 'datetime' in col and ('mid' in col or 'pt' in col)]].head(10))