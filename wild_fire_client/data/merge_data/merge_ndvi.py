import pandas as pd

# 1. 원본(기상+기타) 데이터와 ndvi 데이터 불러오기
df_main = pd.read_csv("fire_weather_merged_full_final_real.csv")
df_ndvi = pd.read_csv("forest_csv/fire_with_ndvi_before.csv")

# 2. merge (fire_date, lat, lng로 매칭)
df_merged = pd.merge(
    df_main,
    df_ndvi[['fire_date', 'lat', 'lng', 'ndvi_before']],  # ndvi만 추가
    on=['fire_date', 'lat', 'lng'],
    how='left'  # main 기준이므로 ndvi 없는 건 NaN 됨
)

# 3. 결과 컬럼만 잠깐 확인 (필요없으면 삭제 가능)
print(df_merged[['fire_date', 'lat', 'lng', 'ndvi_before']].head(10))

# 4. 저장
df_merged.to_csv("fire_weather_merged_full_final_with_ndvi.csv", index=False, encoding='utf-8-sig')
print("병합 및 저장 완료!")