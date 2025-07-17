import pandas as pd
import numpy as np

# 1. 데이터 불러오기
df = pd.read_csv("final_data_features.csv")

# 2. datetime 컬럼 파생 변수 생성
df['start_datetime'] = pd.to_datetime(df['start_datetime'])
df['end_datetime'] = pd.to_datetime(df['end_datetime'])

df['start_year'] = df['start_datetime'].dt.year
df['start_month'] = df['start_datetime'].dt.month
df['start_day'] = df['start_datetime'].dt.day
df['start_hour'] = df['start_datetime'].dt.hour

df['end_year'] = df['end_datetime'].dt.year
df['end_month'] = df['end_datetime'].dt.month
df['end_day'] = df['end_datetime'].dt.day
df['end_hour'] = df['end_datetime'].dt.hour

df['fire_duration_hours'] = (df['end_datetime'] - df['start_datetime']).dt.total_seconds() / 3600
df['start_weekday'] = df['start_datetime'].dt.weekday
df['start_quarter'] = df['start_datetime'].dt.quarter

# 3. 파생 feature 생성
df['T2M_diff'] = df['T2M_end'] - df['T2M_start']
df['RH2M_ratio'] = df['RH2M_end'] / (df['RH2M_start'] + 1e-6)
df['PRECTOTCORR_intensity'] = df['PRECTOTCORR_max'] / (df['PRECTOTCORR_sum'] + 1e-6)
df['treecover_density_effect'] = df['treecover_pre_fire_5x5'] * df['ndvi_before']
df['duration_WS10M'] = df['fire_duration_hours'] * df['WS10M_mean']
df['is_holiday'] = df['start_weekday'].isin([5, 6]).astype(int)
df['fire_season'] = df['start_month'].isin([3,4,5,10,11]).astype(int)
df['extreme_wind'] = (df['WS10M_max'] > 8).astype(int)
df['extreme_temp'] = (df['T2M_max'] > 30).astype(int)

# 4. feature 컬럼 순서 정의
feature_cols = [
    'T2M_mean','T2M_max','T2M_min','T2M_std',
    'RH2M_mean','RH2M_min','RH2M_std',
    'WS2M_mean','WS2M_max','WS2M_std',
    'WS10M_mean','WS10M_max','WS10M_std',
    'WD2M_mean','WD10M_mean',
    'PRECTOTCORR_sum','PRECTOTCORR_max',
    'PS_mean','PS_std',
    'ALLSKY_SFC_SW_DWN_mean','ALLSKY_SFC_SW_DWN_max',
    'T2M_start','T2M_end',
    'RH2M_start','RH2M_end',
    'WS2M_start','WS2M_end',
    'WS10M_start','WS10M_end',
    'WD2M_start','WD2M_end',
    'WD10M_start','WD10M_end',
    'PRECTOTCORR_start','PRECTOTCORR_end',
    'PS_start','PS_end',
    'ALLSKY_SFC_SW_DWN_start','ALLSKY_SFC_SW_DWN_end',
    'start_year','start_month','start_day','start_hour',
    'end_year','end_month','end_day','end_hour',
    'start_weekday','start_quarter',
    'ndvi_before','elevation','slope','aspect','treecover_pre_fire_5x5',
    # 추가 파생 feature
    'T2M_diff','RH2M_ratio','PRECTOTCORR_intensity','treecover_density_effect','duration_WS10M',
    'is_holiday','fire_season','extreme_wind','extreme_temp',
    'fire_duration_hours'
]

target_col = "fire_area"

# 5. 최종 feature + target만 추출
final_df = df[feature_cols + [target_col]].copy()

# 6. 결측치 처리
final_df = final_df.dropna(subset=[target_col])      # target 없는 row는 drop
final_df = final_df.fillna(final_df.mean(numeric_only=True))   # feature 결측치는 평균으로 대체

# 7. 저장
final_df.to_csv("preprocess/csv/ml_ready_data.csv", index=False, encoding="utf-8-sig")
print("ML 파생 feature 데이터 저장 완료! → ml_ready_data.csv")