# import pandas as pd

# # 1. 데이터 불러오기
# df = pd.read_csv("final_data_features.csv")

# # 2. datetime 컬럼 파생 변수 생성
# df['start_datetime'] = pd.to_datetime(df['start_datetime'])
# df['end_datetime'] = pd.to_datetime(df['end_datetime'])

# df['start_year'] = df['start_datetime'].dt.year
# df['start_month'] = df['start_datetime'].dt.month
# df['start_day'] = df['start_datetime'].dt.day
# df['start_hour'] = df['start_datetime'].dt.hour

# df['end_year'] = df['end_datetime'].dt.year
# df['end_month'] = df['end_datetime'].dt.month
# df['end_day'] = df['end_datetime'].dt.day
# df['end_hour'] = df['end_datetime'].dt.hour

# df['fire_duration_hours'] = (df['end_datetime'] - df['start_datetime']).dt.total_seconds() / 3600

# # (선택) 요일, 분기 등도 파생할 수 있음
# df['start_weekday'] = df['start_datetime'].dt.weekday
# df['start_quarter'] = df['start_datetime'].dt.quarter

# # 3. feature 및 target 컬럼 정의
# feature_cols = [
#     # 1. 기후 집계치
#     'T2M_mean', 'T2M_max', 'T2M_min', 'T2M_std',
#     'RH2M_mean', 'RH2M_min', 'RH2M_std',
#     'WS2M_mean', 'WS2M_max', 'WS2M_std',
#     'WS10M_mean', 'WS10M_max', 'WS10M_std',
#     'WD2M_mean', 'WD10M_mean',
#     'PRECTOTCORR_sum', 'PRECTOTCORR_max',
#     'PS_mean', 'PS_std',
#     'ALLSKY_SFC_SW_DWN_mean', 'ALLSKY_SFC_SW_DWN_max',
#     # 2. start/end 원본값
#     'T2M_start', 'T2M_end',
#     'RH2M_start', 'RH2M_end',
#     'WS2M_start', 'WS2M_end',
#     'WS10M_start', 'WS10M_end',
#     'WD2M_start', 'WD2M_end',
#     'WD10M_start', 'WD10M_end',
#     'PRECTOTCORR_start', 'PRECTOTCORR_end',
#     'PS_start', 'PS_end',
#     'ALLSKY_SFC_SW_DWN_start', 'ALLSKY_SFC_SW_DWN_end',
#     # 3. 파생 datetime 변수
#     'start_year', 'start_month', 'start_day', 'start_hour',
#     'end_year', 'end_month', 'end_day', 'end_hour',
#     'fire_duration_hours', 'start_weekday', 'start_quarter',
#     # 4. 산림/지형 feature
#     'ndvi_before', 'elevation', 'slope', 'aspect', 'treecover_pre_fire_5x5'
# ]

# target_col = "fire_area"

# # 4. 최종 feature + target만 추출
# final_df = df[feature_cols + [target_col]].copy()

# # 5. (선택) 결측치 처리
# final_df = final_df.dropna(subset=[target_col])   # target 없는 row는 무조건 drop!
# final_df = final_df.fillna(final_df.mean())      # feature 결측치는 평균으로 대체 (혹은 원하는 방식으로!)

# # 6. 저장
# final_df.to_csv("preprocess/csv/ml_ready_data.csv", index=False, encoding="utf-8-sig")
# print("ML 파생 feature 데이터 저장 완료! → ml_ready_data.csv")

import pandas as pd

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

# 3. feature 및 target 컬럼 정의
feature_cols = [
    'T2M_mean', 'T2M_max', 'T2M_min', 'T2M_std',
    'RH2M_mean', 'RH2M_min', 'RH2M_std',
    'WS2M_mean', 'WS2M_max', 'WS2M_std',
    'WS10M_mean', 'WS10M_max', 'WS10M_std',
    'WD2M_mean', 'WD10M_mean',
    'PRECTOTCORR_sum', 'PRECTOTCORR_max',
    'PS_mean', 'PS_std',
    'ALLSKY_SFC_SW_DWN_mean', 'ALLSKY_SFC_SW_DWN_max',
    'T2M_start', 'T2M_end',
    'RH2M_start', 'RH2M_end',
    'WS2M_start', 'WS2M_end',
    'WS10M_start', 'WS10M_end',
    'WD2M_start', 'WD2M_end',
    'WD10M_start', 'WD10M_end',
    'PRECTOTCORR_start', 'PRECTOTCORR_end',
    'PS_start', 'PS_end',
    'ALLSKY_SFC_SW_DWN_start', 'ALLSKY_SFC_SW_DWN_end',
    'start_year', 'start_month', 'start_day', 'start_hour',
    'end_year', 'end_month', 'end_day', 'end_hour',
    'fire_duration_hours', 'start_weekday', 'start_quarter',
    'ndvi_before', 'elevation', 'slope', 'aspect', 'treecover_pre_fire_5x5'
]

target_col = "fire_area"

# 4. 최종 feature + target만 추출
final_df = df[feature_cols + [target_col]].copy()

# 5. 결측치 처리
final_df = final_df.dropna(subset=[target_col])  # target 없는 row는 무조건 drop!
final_df = final_df.fillna(final_df.mean())      # feature 결측치는 평균으로 대체

# 6. 저장
final_df.to_csv("preprocess/csv/ml_ready_data.csv", index=False, encoding="utf-8-sig")
print("ML 파생 feature 데이터 저장 완료! → ml_ready_data.csv")