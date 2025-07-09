import ee
import pandas as pd
from datetime import datetime, timedelta

# 1. Earth Engine 인증 및 초기화
ee.Authenticate()
ee.Initialize(project='deep-theorem-456805-p2')

# 2. Sentinel-2 결과 파일 읽기
df = pd.read_csv("fire_with_ndvi_sentinel.csv")
print(f"전체 데이터: {len(df)}개")

# 3. MODIS NDVI만 필요한 행(즉 ndvi 결측) 대상으로만 계산
modis_ndvi_list = []
count = 0
for idx, row in df.iterrows():
    fire_date = str(row['fire_date'])
    lat = float(row['lat'])
    lng = float(row['lng'])
    ndvi = row['ndvi'] if 'ndvi' in row and not pd.isnull(row['ndvi']) else None

    # 이미 Sentinel-2 NDVI가 있으면 MODIS 계산 없이 None으로 남겨둠
    if ndvi is not None:
        modis_ndvi_list.append(None)
        continue

    # Sentinel-2 NDVI 결측인 경우만 MODIS NDVI 추출
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

# 4. MODIS NDVI 컬럼 추가
df['modis_ndvi'] = modis_ndvi_list

# 5. 결과 저장 (Sentinel-2 NDVI+MODIS NDVI 컬럼 모두)
df.to_csv('fire_with_ndvi_modis.csv', index=False, encoding='utf-8-sig')
print(f"MODIS NDVI 결측보정 추출 완료: {len(df)}건 (fire_with_ndvi_modis.csv)")