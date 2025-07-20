import pandas as pd
import numpy as np
import sys
import os

# 유틸 함수 모듈 경로 추가 (서브폴더 구조일 때)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.fwi_calc import fwi_calc  # 만약 없으면 이 부분만 직접 구현/주석!

# === 1. 데이터 로드 ===
df = pd.read_csv("gangwon_fire_dem_slope_aspect_window.csv")  # 파일명만 맞게!

EPS = 1e-6  # Zero division 방지

# === 2. 불필요한 문자형/주소/행정구역 컬럼 제거 ===
drop_cols = [
    'gungu', 'eupmyeon', 'dongri', 'jibun', 'locsi', 'matched_address',
    'lat', 'lng',
    # 'fire_date',  # 계절 파생 뒤에 삭제!
]
df = df.drop(columns=[col for col in drop_cols if col in df.columns])

# === 3. 관측치 없음(NaN) 변환: 0.0 → NaN (기상 변수만!) ===
weather_cols = [
    col for col in df.columns
    if any(x in col for x in [
        'T2M_', 'RH2M_', 'WS2M_', 'WS10M_', 'PRECTOTCORR_', 'WD2M_', 'WD10M_'
    ])
]
for col in weather_cols:
    df[col] = df[col].replace(0.0, np.nan)

# === 4. 기본 피처 파생 ===
df['dry_windy_combo'] = df['dry_days_30d_start'] * df['WS10M_0h']
df['hot_dry_combo'] = df['T2M_0h'] / (df['RH2M_0h'] + EPS)
df['fuel_combo'] = df['treecover_pre_fire_5x5'] * df['ndvi_before']
df['slope_south_combo'] = df['slope_mean'] * df['aspect_south_ratio']
df['potential_spread_index'] = df['dry_windy_combo'] * df['fuel_combo']
df['treecover_var_effect'] = df['treecover_pre_fire_5x5']
df['terrain_var_effect'] = df['elevation_std'] + df['slope_std']
df['south_steep_effect'] = df['slope_max'] * df['aspect_south_ratio']

# === 5. 기후 시계열 변동성 (0~12h, 5개 시점만!) ===
for var in ['WS10M', 'T2M', 'RH2M', 'WD10M']:
    try:
        cols = [f"{var}_{h}h" for h in [0, 3, 6, 9, 12] if f"{var}_{h}h" in df.columns]
        if len(cols) >= 2:
            df[f"{var}_std"] = df[cols].std(axis=1)
    except Exception as e:
        print(f"변동성 계산 에러: {var}", e)

# === 6. 최고/최저 값 피처 ===
try:
    ws_cols = [f'WS10M_{h}h' for h in [0, 3, 6, 9, 12] if f'WS10M_{h}h' in df.columns]
    rh_cols = [f'RH2M_{h}h' for h in [0, 3, 6, 9, 12] if f'RH2M_{h}h' in df.columns]
    t2m_cols = [f'T2M_{h}h' for h in [0, 3, 6, 9, 12] if f'T2M_{h}h' in df.columns]
    if ws_cols: df['max_wind'] = df[ws_cols].max(axis=1)
    if rh_cols: df['min_humidity'] = df[rh_cols].min(axis=1)
    if t2m_cols: df['max_temp'] = df[t2m_cols].max(axis=1)
except Exception as e:
    print("최고/최저값 에러:", e)

# === 7. 풍향/풍속 일관성 ===
try:
    wd_cols = [f'WD10M_{h}h' for h in [0, 3, 6, 9, 12] if f'WD10M_{h}h' in df.columns]
    if wd_cols:
        df['WD10M_var'] = df[wd_cols].std(axis=1)
    if 'WS10M_std' in df.columns and 'WD10M_var' in df.columns:
        df['wind_steady'] = ((df['WS10M_std'] < 2) & (df['WD10M_var'] < 30)).astype(int)
except Exception as e:
    print("풍향/풍속 일관성 에러:", e)

# === 8. 연속 무강수/누적강수 비율 ===
df['dry_to_rain_ratio'] = df['dry_days_30d_start'] / (df['total_precip_30d_start'] + EPS)

# === 9. NDVI 스트레스 ===
NDVI_BASELINE = 0.7
df['ndvi_stress'] = NDVI_BASELINE - df['ndvi_before']

# === 10. 산불 위험 종합 점수 ===
if set(['dry_windy_combo', 'hot_dry_combo', 'max_wind', 'ndvi_stress', 'slope_south_combo', 'treecover_pre_fire_5x5']).issubset(df.columns):
    df['fire_risk_score_raw'] = (
        0.25 * df['dry_windy_combo'] +
        0.25 * df['hot_dry_combo'] +
        0.15 * df['max_wind'] +
        0.15 * df['ndvi_stress'] +
        0.10 * df['slope_south_combo'] +
        0.10 * df['treecover_pre_fire_5x5']
    )
    df['fire_risk_score'] = (df['fire_risk_score_raw'] - df['fire_risk_score_raw'].min()) / (df['fire_risk_score_raw'].max() - df['fire_risk_score_raw'].min() + EPS)

# === 11. 계절성 파생 + fire_date 삭제 ===
try:
    if 'fire_date' in df.columns:
        df['fire_month'] = pd.to_datetime(df['fire_date']).dt.month
        df['is_spring'] = df['fire_month'].isin([3,4,5]).astype(int)
        df['is_autumn'] = df['fire_month'].isin([9,10,11]).astype(int)
        df = df.drop(columns=['fire_date'])
except Exception as e:
    print("계절성 파생 에러:", e)

# === 12. 시계열 급변 Feature ===
try:
    if set(['WS10M_0h','WS10M_12h']).issubset(df.columns):
        df['wind_change'] = df['WS10M_12h'] - df['WS10M_0h']
    if set(['T2M_0h','T2M_12h']).issubset(df.columns):
        df['temp_change'] = df['T2M_12h'] - df['T2M_0h']
    if set(['RH2M_0h','RH2M_12h']).issubset(df.columns):
        df['humid_change'] = df['RH2M_12h'] - df['RH2M_0h']
except Exception as e:
    print("시계열 급변 에러:", e)

# === 13. 이상치/경계치 플래그 ===
df['high_wind_flag'] = (df.get('max_wind', 0) > 7).astype(int)
df['low_humidity_flag'] = (df.get('min_humidity', 100) < 30).astype(int)
df['extreme_hot_flag'] = (df.get('max_temp', 0) > 33).astype(int)

# === 14. FWI 계산 ===
try:
    def safe_fwi_calc(row):
        try:
            T = row.get('T2M_0h', np.nan)
            RH = row.get('RH2M_0h', np.nan)
            W = row.get('WS10M_0h', np.nan)
            P = row.get('PRECTOTCORR_0h', 0)
            month = row.get('fire_month', 6)  # 이미 파생된 fire_month 사용
            res = fwi_calc(T=T, RH=RH, W=W, P=P, month=month, FFMC0=85, DMC0=6, DC0=15)
            return res.get('FWI', np.nan)
        except Exception:
            return np.nan

    df['fwi_0h'] = df.apply(safe_fwi_calc, axis=1)

    def mean_fwi(row):
        vals = []
        for h in [0,3,6,9,12]:
            try:
                T = row.get(f'T2M_{h}h', np.nan)
                RH = row.get(f'RH2M_{h}h', np.nan)
                W = row.get(f'WS10M_{h}h', np.nan)
                P = row.get(f'PRECTOTCORR_{h}h', 0)
                month = row.get('fire_month', 6)
                res = fwi_calc(T=T, RH=RH, W=W, P=P, month=month, FFMC0=85, DMC0=6, DC0=15)
                fwi = res.get('FWI', np.nan)
                if not np.isnan(fwi):
                    vals.append(fwi)
            except: continue
        return np.mean(vals) if vals else np.nan

    df['fwi_mean_0_12h'] = df.apply(mean_fwi, axis=1)

except ImportError:
    print("pyfwi 라이브러리 없음! FWI Proxy로 대체")
    df['fwi_proxy_0h'] = df['T2M_0h'] * df['WS10M_0h'] * (100 - df['RH2M_0h']) / 1000
    proxy_cols = [f'T2M_{h}h' for h in [0,3,6,9,12] if f'T2M_{h}h' in df.columns]
    if proxy_cols:
        fwi_proxy_list = []
        for h in [0,3,6,9,12]:
            if f'T2M_{h}h' in df.columns and f'WS10M_{h}h' in df.columns and f'RH2M_{h}h' in df.columns:
                proxy = df[f'T2M_{h}h'] * df[f'WS10M_{h}h'] * (100 - df[f'RH2M_{h}h']) / 1000
                fwi_proxy_list.append(proxy)
        if fwi_proxy_list:
            df['fwi_proxy_mean'] = np.mean(fwi_proxy_list, axis=0)

# === 15. NaN/Inf 처리 (NaN 유지!) ===
df = df.replace([np.inf, -np.inf], np.nan)
# ★ 절대 fillna(0) 쓰지 않음!

# === 16. 저장 ===
df.to_csv("final_merged_feature_engineered.csv", index=False, encoding="utf-8-sig")
print("산불 확산 파생 feature 생성 및 저장 완료! → final_merged_feature_engineered.csv")