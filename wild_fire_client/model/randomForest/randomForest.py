import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
import numpy as np

# 1. 데이터 불러오기
df = pd.read_csv("ml_ready_data.csv")

# 2. feature/target 분리
feature_cols = [
    'T2M_mean','T2M_max','T2M_min','T2M_std',
    'RH2M_mean','RH2M_min','RH2M_std',
    'WS2M_mean','WS2M_max','WS2M_std',
    'WS10M_mean','WS10M_max','WS10M_std',
    'WD2M_mean','WD10M_mean',
    'PRECTOTCORR_sum','PRECTOTCORR_max',
    'PS_mean','PS_std',
    'ALLSKY_SFC_SW_DWN_mean','ALLSKY_SFC_SW_DWN_max',
    'T2M_start','T2M_end','RH2M_start','RH2M_end',
    'WS2M_start','WS2M_end','WS10M_start','WS10M_end',
    'WD2M_start','WD2M_end','WD10M_start','WD10M_end',
    'PRECTOTCORR_start','PRECTOTCORR_end',
    'PS_start','PS_end',
    'ALLSKY_SFC_SW_DWN_start','ALLSKY_SFC_SW_DWN_end',
    'start_year','start_month','start_day','start_hour',
    'end_year','end_month','end_day','end_hour',
    'fire_duration_hours','start_weekday','start_quarter',
    'ndvi_before','elevation','slope','aspect','treecover_pre_fire_5x5'
]
target_col = "fire_area"

X = df[feature_cols]
y = df[target_col]

# 3. 데이터 분리 (train: 80%, test: 20%)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. 모델 생성 및 학습
model = RandomForestRegressor(
    n_estimators=100,      # 트리 개수
    max_depth=None,        # 트리 최대 깊이(제한 없음)
    random_state=42,
    n_jobs=-1              # CPU 코어 모두 사용
)
model.fit(X_train, y_train)

# 5. 예측 및 평가
y_pred = model.predict(X_test)
rmse = mean_squared_error(y_test, y_pred, squared=False)
r2 = r2_score(y_test, y_pred)

print(f"테스트 RMSE: {rmse:.3f}")
print(f"테스트 R^2: {r2:.3f}")

# 6. (선택) feature 중요도 시각화
importances = model.feature_importances_
indices = np.argsort(importances)[::-1]

plt.figure(figsize=(10, 8))
plt.title("Feature Importance (RandomForest)")
plt.bar(range(len(feature_cols)), importances[indices])
plt.xticks(range(len(feature_cols)), [feature_cols[i] for i in indices], rotation=90)
plt.tight_layout()
plt.show()