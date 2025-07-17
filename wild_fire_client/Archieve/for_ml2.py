import numpy as np
import pandas as pd

# 기존 데이터프레임 불러오기
df = pd.read_csv("preprocess/csv/ml_ready_data.csv")
df['T2M_diff'] = df['T2M_end'] - df['T2M_start']
df['RH2M_ratio'] = df['RH2M_min'] / (df['RH2M_mean'] + 1e-6)
# df['WS2M_range'] = df['WS2M_max'] - df['WS2M_min']  # ← 이 줄은 주석처리
df['PRECTOTCORR_intensity'] = df['PRECTOTCORR_max'] / (df['PRECTOTCORR_sum'] + 1e-6)

# 2. 조합 Feature
df['treecover_density_effect'] = df['treecover_pre_fire_5x5'] * df['ndvi_before']
df['duration_WS10M'] = df['fire_duration_hours'] * df['WS10M_mean']

# 3. 시간/캘린더 특성
df['is_holiday'] = df['start_weekday'].isin([5,6]).astype(int)
df['fire_season'] = df['start_month'].isin([3,4,5,10,11]).astype(int)

# 4. 극단/이상치 특성
df['extreme_wind'] = (df['WS10M_max'] > 8).astype(int)
df['extreme_temp'] = (df['T2M_max'] > 30).astype(int)

# ★★★ 파생변수 포함 새 파일로 저장 ★★★
df.to_csv("preprocess/csv/final_data_with_features_ready.csv", index=False, encoding='utf-8-sig')
print("저장 완료: final_data_with_features.csv")