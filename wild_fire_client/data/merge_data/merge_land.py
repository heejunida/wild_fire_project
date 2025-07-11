import pandas as pd

# 1. 파일 경로 지정
main_csv = "fire_weather_merged_full_final_with_ndvi.csv"
dem_csv = "land_csv/gangwon_fire_dem_slope_aspect.csv"

# 2. 파일 읽기
main_df = pd.read_csv(main_csv, encoding='utf-8-sig')
dem_df = pd.read_csv(dem_csv, encoding='utf-8-sig')

# 3. 좌표(소수점 4자리) 기준 컬럼 생성
main_df['lat_r'] = main_df['lat'].round(4)
main_df['lng_r'] = main_df['lng'].round(4)
dem_df['lat_r'] = dem_df['lat'].round(4)
dem_df['lng_r'] = dem_df['lng'].round(4)

# 4. 병합 (좌표만 기준)
merged = pd.merge(
    main_df,
    dem_df[['lat_r', 'lng_r', 'elevation', 'slope', 'aspect']],
    on=['lat_r', 'lng_r'],
    how='left'
)

# 5. 임시 좌표 컬럼 삭제
merged.drop(['lat_r', 'lng_r'], axis=1, inplace=True)

# 6. 파일 저장
out_csv = "fire_weather_merged_full_final_with_ndvi_dem.csv"
merged.to_csv(out_csv, index=False, encoding='utf-8-sig')

print(f"최종 저장 완료: {out_csv} (shape: {merged.shape})")