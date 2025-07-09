import ee
import pandas as pd
from datetime import datetime, timedelta

# 1. Earth Engine 인증 및 초기화
ee.Authenticate()
ee.Initialize(project='deep-theorem-456805-p2')

# 2. 전체 산불 데이터 파일 읽기 (fire_with_ndvi_sentinel.csv 또는 gangwon_fire_ml_input.csv 등)
df = pd.read_csv("gangwon_fire_ml_input.csv")  # 원본 화재 데이터 기준, 컬럼 변경 가능

print(f"전체 데이터: {len(df)}개")

modis_ndvi_list = []
count = 0

for idx, row in df.iterrows():
    fire_date = str(row['fire_date'])
    lat = float(row['lat'])
    lng = float(row['lng'])

    try:
        date_obj = datetime.strptime(fire_date, '%Y-%m-%d')
        start_date = (date_obj - timedelta(days=8)).strftime('%Y-%m-%d')
        end_date = (date_obj + timedelta(days=8)).strftime('%Y-%m-%d')
        modis = ee.ImageCollection("MODIS/061/MOD13Q1") \
            .filterDate(start_date, end_date) \
            .filterBounds(ee.Geometry.Point(lng, lat))
        image = modis.first()
        if image is None:
            ndvi_modis = None
        else:
            ndvi_val = image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=ee.Geometry.Point(lng, lat),
                scale=250
            ).get('NDVI').getInfo()
            if ndvi_val is not None:
                ndvi_modis = float(ndvi_val) / 10000.0
            else:
                ndvi_modis = None
    except Exception as e:
        print(f"MODIS NDVI 추출 실패: {lat}, {lng}, {fire_date} - {e}")
        ndvi_modis = None

    modis_ndvi_list.append(ndvi_modis)
    count += 1
    if count % 100 == 0:
        print(f"[MODIS] {count}개 처리 완료")

# 4. MODIS NDVI 컬럼 추가 (혹시 컬럼 이미 있으면 덮어씀)
df['modis_ndvi'] = modis_ndvi_list

# 5. 결과 저장
df.to_csv('fire_with_ndvi_modis.csv', index=False, encoding='utf-8-sig')
print(f"MODIS NDVI 전체 추출 완료: {len(df)}건 (fire_with_ndvi_modis.csv)")