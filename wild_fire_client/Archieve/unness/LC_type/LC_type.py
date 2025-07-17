import ee
import pandas as pd
from datetime import datetime

# 1. Earth Engine 인증 및 초기화
ee.Authenticate()
ee.Initialize(project='deep-theorem-456805-p2')   # 본인 GCP 프로젝트명으로!

# 2. 산불이력 데이터 불러오기
in_csv = "fire_csv/gangwon_fire_ml_input.csv"
df = pd.read_csv(in_csv, encoding='utf-8-sig')

forest_types_mode_5x5 = []
for idx, row in df.iterrows():
    lat, lng = float(row['lat']), float(row['lng'])
    year = int(row['startyear'])

    try:
        # (1) 해당 연도 LC_Type1 이미지 뽑기
        img = ee.ImageCollection("MODIS/061/MCD12Q1") \
            .filterDate(f"{year}-01-01", f"{year}-12-31") \
            .filterBounds(ee.Geometry.Point(lng, lat)) \
            .first()
        if img is None:
            forest_type_mode = None
        else:
            # (2) 5x5 그리드(2=5x5 픽셀)의 mode 계산
            mode_img = img.select('LC_Type1').reduceNeighborhood(
                reducer=ee.Reducer.mode(),
                kernel=ee.Kernel.square(2),  # 5x5 window (2=5x5)
                inputWeight=None,
                skipMasked=True
            )
            val = mode_img.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=ee.Geometry.Point(lng, lat),
                scale=500,
                maxPixels=1e8
            ).get('LC_Type1_mode').getInfo()
            forest_type_mode = int(val) if val is not None else None
    except Exception as e:
        print(f"[{idx+1}] 5x5 최빈 산림유형 추출 실패: {lat}, {lng}, {year} - {e}")
        forest_type_mode = None

    forest_types_mode_5x5.append(forest_type_mode)
    if (idx + 1) % 100 == 0:
        print(f"[MODIS 5x5 mode] {idx+1}건 처리 완료")

# 3. 결과 컬럼 추가/저장
df['forest_type_mode_5x5'] = forest_types_mode_5x5
out_csv = "fire_with_forest_type_mode5x5.csv"
df.to_csv(out_csv, index=False, encoding='utf-8-sig')
print(f"최종 저장 완료: {out_csv} ({len(df)}건)")