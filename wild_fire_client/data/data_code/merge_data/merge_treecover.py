import pandas as pd

# 1. 파일 불러오기
main = pd.read_csv("merge_process/fire_weather_merged_full_final_with_ndvi_dem_forest.csv", encoding="utf-8-sig")  # 메인 파일
treecover = pd.read_csv("forest_csv/fire_with_treecover_pre_fire_5x5.csv", encoding="utf-8-sig")  # 산림률(병합용)

# 1-1. 위경도 소수점 자릿수 맞추기(필요시) → 여기선 7자리로 통일 예시
main['lat'] = main['lat'].round(7)
main['lng'] = main['lng'].round(7)
treecover['lat'] = treecover['lat'].round(7)
treecover['lng'] = treecover['lng'].round(7)

# 2. 병합 기준 키
key_cols = ['lat', 'lng', 'fire_date']

# 2-1. main, treecover 모두 중복 제거!
main = main.drop_duplicates(subset=key_cols)
treecover = treecover.drop_duplicates(subset=key_cols)

# 3. 필요한 컬럼만 남기기
treecover_sub = treecover[key_cols + ['treecover_pre_fire_5x5']]

# 4. 병합(메인 기준 left join)
merged = pd.merge(main, treecover_sub, on=key_cols, how='left')

# 5. 확인
print(f"병합 후 행 수: {len(merged)}")
print(merged.head())

# 6. 저장 (CSV & Excel)
merged.to_csv("all_data_merged_with_treecover.csv", index=False, encoding='utf-8-sig')
merged.to_excel("all_data_merged_with_treecover.xlsx", index=False)

print("병합/저장 완료! (엑셀까지)")