import ee
import pandas as pd

ee.Authenticate()
ee.Initialize(project='deep-theorem-456805-p2')  # 본인 GCP 프로젝트명으로 수정하세요

# 1. 기존 CSV 불러오기
in_csv = "all_data_merged_with_treecover.csv"  # 기존 처리 결과 파일 경로
df = pd.read_csv(in_csv, encoding='utf-8-sig')

# 2. 결측값 있는 행만 추출
df_missing = df[df['forest_type_mode_5x5'].isna()].copy()
print(f"재처리할 결측 데이터 개수: {len(df_missing)}")

def fetch_forest_mode(lat, lng, year):
    search_year = year
    for _ in range(5):  # 최대 5년 이내 fallback
        try:
            img_col = ee.ImageCollection("MODIS/061/MCD12Q1") \
                .filterDate(f"{search_year}-01-01", f"{search_year}-12-31") \
                .filterBounds(ee.Geometry.Point(lng, lat)) \
                .first()
            if img_col is None or img_col.getInfo() is None:
                search_year -= 1
                continue

            mode_img = img_col.select('LC_Type1').reduceNeighborhood(
                reducer=ee.Reducer.mode(),
                kernel=ee.Kernel.square(2),  # 5x5 픽셀 영역
                inputWeight=None,
                skipMasked=True
            )
            val = mode_img.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=ee.Geometry.Point(lng, lat),
                scale=500,
                maxPixels=1e8
            ).get('LC_Type1_mode').getInfo()
            if val is not None:
                return int(val)
            else:
                search_year -= 1
        except Exception as e:
            print(f"좌표({lat},{lng}), 연도 {search_year} 조회 실패: {e}")
            search_year -= 1
    return None

# 3. 결측값 보완 수행
updated_values = []
for idx, row in df_missing.iterrows():
    lat = float(row['lat'])
    lng = float(row['lng'])
    year = int(row['startyear'])

    # 2024년도면 2023 fallback 로직 포함
    target_year = year
    if year == 2024:
        target_year = 2024  # 우선 2024로 시도하고 없으면 2023으로 fallback 할 것임

    val = fetch_forest_mode(lat, lng, target_year)
    if val is None and year == 2024:
        val = fetch_forest_mode(lat, lng, 2023)
    print(f"[{idx+1}] 좌표({lat},{lng}), 원본년도 {year} -> 보완 산림유형: {val}")
    updated_values.append(val)

# 4. 원본 DataFrame에 결측 보완값 업데이트
df.loc[df['forest_type_mode_5x5'].isna(), 'forest_type_mode_5x5'] = updated_values

# 5. 최종 파일 저장
out_csv = "fire_with_forest_type_mode5x5_filled.csv"
df.to_csv(out_csv, index=False, encoding='utf-8-sig')
print(f"결측 보완 후 최종 저장 완료: {out_csv}")