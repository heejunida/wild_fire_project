# import pandas as pd

# # 1. 파일 경로
# main_csv = "fire_weather_merged_full_final_with_ndvi_dem.csv"
# forest_type_csv = "fire_with_forest_type_mode5x5.csv"

# # 2. 파일 읽기
# main_df = pd.read_csv(main_csv, encoding='utf-8-sig')
# forest_df = pd.read_csv(forest_type_csv, encoding='utf-8-sig')

# # 3. 좌표 소수점 4자리(또는 5자리)로 맞추기
# main_df['lat_r'] = main_df['lat'].round(4)
# main_df['lng_r'] = main_df['lng'].round(4)
# forest_df['lat_r'] = forest_df['lat'].round(4)
# forest_df['lng_r'] = forest_df['lng'].round(4)

# # 4. 날짜(포맷이 다르면 str로 변환)
# main_df['fire_date'] = main_df['fire_date'].astype(str)
# forest_df['fire_date'] = forest_df['fire_date'].astype(str)

# # 5. 병합
# merged = pd.merge(
#     main_df,
#     forest_df[['lat_r', 'lng_r', 'fire_date', 'forest_type_mode_5x5']],
#     on=['lat_r', 'lng_r', 'fire_date'],
#     how='left'
# )

# # 6. 임시 좌표 컬럼 삭제
# merged.drop(['lat_r', 'lng_r'], axis=1, inplace=True)

# # 7. 저장
# out_csv = "fire_weather_merged_full_final_with_ndvi_dem_forest.csv"
# merged.to_csv(out_csv, index=False, encoding='utf-8-sig')
# print(f"최종 저장 완료: {out_csv} (shape: {merged.shape})")

import pandas as pd

# 1. 파일 경로
main_csv = "fire_weather_merged_full_final_with_ndvi_dem_forest.csv"
treecover_csv = "fire_with_treecover_mean5x5.csv"

# 2. 파일 읽기
main_df = pd.read_csv(main_csv, encoding='utf-8-sig')
treecover_df = pd.read_csv(treecover_csv, encoding='utf-8-sig')

# 3. 좌표 소수점 4자리(또는 5자리)로 맞추기
main_df['lat_r'] = main_df['lat'].round(4)
main_df['lng_r'] = main_df['lng'].round(4)
treecover_df['lat_r'] = treecover_df['lat'].round(4)
treecover_df['lng_r'] = treecover_df['lng'].round(4)

# 4. 날짜(포맷 통일)
main_df['fire_date'] = main_df['fire_date'].astype(str)
treecover_df['fire_date'] = treecover_df['fire_date'].astype(str)

# 5. 병합
merged = pd.merge(
    main_df,
    treecover_df[['lat_r', 'lng_r', 'fire_date', 'treecover2000_mean_5x5', 'treecover_used_year']],
    on=['lat_r', 'lng_r', 'fire_date'],
    how='left'
)

# 6. 임시 좌표 컬럼 삭제
merged.drop(['lat_r', 'lng_r'], axis=1, inplace=True)

# 7. 저장
out_csv = "fire_weather_merged_full_final_with_ndvi_dem_forest_treecover.csv"
merged.to_csv(out_csv, index=False, encoding='utf-8-sig')
print(f"최종 저장 완료: {out_csv} (shape: {merged.shape})")