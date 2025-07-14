import pandas as pd

# --- 1. 데이터 로드
df = pd.read_csv('fire_weather_merged_full_final_real.csv')

# --- 2. 화재 시작/종료 시각 조합 (예시: date_start, hour_start, date_end, hour_end)
# hour이 한자리면 zfill(2)로 0채워서 시각으로 변환
def dt_col(date_col, hour_col):
    # 예: 20111101.0, 15.0 → 2011-11-01 15:00:00
    date_str = df[date_col].astype(str).str.slice(0,8)
    hour_str = df[hour_col].astype(str).str.replace('.0','').str.zfill(2)
    return pd.to_datetime(date_str + ' ' + hour_str, errors='coerce', format='%Y%m%d %H')

df['fire_start'] = dt_col('date_start', 'hour_start')
df['fire_end'] = dt_col('date_end', 'hour_end')
df['duration_hours'] = (df['fire_end'] - df['fire_start']).dt.total_seconds() / 3600

# --- 3. 구간별(예시)
# mid, pt1~pt10 등 필요조건 설정: (예시: 6시간 이상 → mid, 3시간 이상 → pt1 등)
cond_need_mid = df['duration_hours'] >= 6
cond_need_ptN = df['duration_hours'] >= 3

df_need_mid = df[cond_need_mid]
df_need_ptN = df[cond_need_ptN]

# --- 4. 결측/빈값 체크 함수
def null_blank_count(series):
    n_null = series.isnull().sum()
    n_blank = (series == '').sum()
    return n_null, n_blank

# --- 5. mid 결측 체크
for col in ['WS10M_mid', 'WD10M_mid']:
    n_null, n_blank = null_blank_count(df_need_mid[col])
    print(f"[mid] {col}: NaN={n_null} / Blank={n_blank}")

# --- 6. pt1~pt10 결측 체크 (원하면 pt1~ptN까지 반복)
for i in range(1, 11):  # pt1~pt10
    ws_col = f'WS10M_pt{i}'
    wd_col = f'WD10M_pt{i}'
    if ws_col in df_need_ptN.columns:
        n_null_ws, n_blank_ws = null_blank_count(df_need_ptN[ws_col])
        n_null_wd, n_blank_wd = null_blank_count(df_need_ptN[wd_col])
        print(f"[pt{i}] {ws_col}: NaN={n_null_ws} / Blank={n_blank_ws}")
        print(f"[pt{i}] {wd_col}: NaN={n_null_wd} / Blank={n_blank_wd}")

# --- 7. 누적강수량/무강수일수 (전 행 모두 필요하다면 전체 df에서 체크)
for col in ['total_precip_7d', 'total_precip_14d', 'total_precip_30d', 'total_precip_60d', 'total_precip_90d',
            'no_rain_days_7d', 'no_rain_days_14d', 'no_rain_days_30d', 'no_rain_days_60d', 'no_rain_days_90d']:
    n_null, n_blank = null_blank_count(df[col])
    print(f"{col}: NaN={n_null} / Blank={n_blank}")

# --- 8. 결측 row 예시 추출 (필요할 때)
for col in ['WS10M_mid', 'WD10M_mid']:
    null_rows = df_need_mid[df_need_mid[col].isnull()]
    if not null_rows.empty:
        print(f"[결측] {col} 결측 row 예시 (최대 3개):")
        print(null_rows[[col, 'date_mid', 'hour_mid', 'lat', 'lng']].head(3))

for i in range(1, 11):
    ws_col = f'WS10M_pt{i}'
    wd_col = f'WD10M_pt{i}'
    for col in [ws_col, wd_col]:
        if col in df_need_ptN.columns:
            null_rows = df_need_ptN[df_need_ptN[col].isnull()]
            if not null_rows.empty:
                print(f"[결측] {col} 결측 row 예시 (최대 3개):")
                print(null_rows[[col, f'date_pt{i}', f'hour_pt{i}', 'lat', 'lng']].head(3))