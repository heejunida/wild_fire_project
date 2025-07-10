import ee
import pandas as pd
from datetime import datetime

# 1. Earth Engine 인증 및 초기화
ee.Authenticate()
ee.Initialize(project='deep-theorem-456805-p2')   # 본인 GCP 프로젝트명으로!

# 2. 산불이력 데이터 불러오기
in_csv = "gangwon_fire_ml_input.csv"
df = pd.read_csv(in_csv, encoding='utf-8-sig')

forest_types = []
for idx, row in df.iterrows():
    lat, lng = float(row['lat']), float(row['lng'])
    # 연도 정보 기준 (MODIS는 2001~2023)
    year = int(row['startyear'])
    date_str = f"{year}-07-01"   # LC_Type1은 해마다 7월1일로 처리(관례)
    try:
        img = ee.ImageCollection("MODIS/061/MCD12Q1") \
            .filterDate(f"{year}-01-01", f"{year}-12-31") \
            .filterBounds(ee.Geometry.Point(lng, lat)) \
            .first()
        if img is None:
            forest_type = None
        else:
            # LC_Type1: 1=침엽수, 2=활엽수, 3=혼효, 4=관목, 5=초지, ...
            val = img.select('LC_Type1').reduceRegion(
                reducer=ee.Reducer.mode(),
                geometry=ee.Geometry.Point(lng, lat),
                scale=500
            ).get('LC_Type1').getInfo()
            forest_type = int(val) if val is not None else None
    except Exception as e:
        print(f"[{idx+1}] 산림유형 추출 실패: {lat}, {lng}, {year} - {e}")
        forest_type = None

    forest_types.append(forest_type)
    if (idx + 1) % 100 == 0:
        print(f"[MODIS] {idx+1}건 처리 완료")

# 3. 결과 컬럼 추가/저장
df['forest_type'] = forest_types
out_csv = "fire_with_forest_type.csv"
df.to_csv(out_csv, index=False, encoding='utf-8-sig')
print(f"최종 저장 완료: {out_csv} ({len(df)}건)")