from datetime import datetime, UTC
import ee
import pandas as pd
from datetime import datetime, timedelta

# 1. Earth Engine 인증 및 초기화
ee.Authenticate()
ee.Initialize(project='deep-theorem-456805-p2')

# 2. 산불 데이터 읽기 (fire_date, lat, lng 필수)
df = pd.read_csv("gangwon_fire_ml_input.csv")
print(f"전체 데이터: {len(df)}개")

ndvi_before_list = []
ndvi_before_date_list = []
ndvi_before_days_list = []
count = 0

for idx, row in df.iterrows():
    fire_date = str(row['fire_date'])
    lat = float(row['lat'])
    lng = float(row['lng'])

    try:
        fire_dt = datetime.strptime(fire_date, '%Y-%m-%d')
        # “산불 발생 30일 전 ~ 1일 전” 기간 NDVI 뽑기
        start_date = (fire_dt - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = (fire_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        pt = ee.Geometry.Point(lng, lat)
        ndvi_ic = ee.ImageCollection("MODIS/061/MOD13Q1") \
            .filterDate(start_date, end_date) \
            .filterBounds(pt) \
            .sort('system:time_start', False)  # 최신순 정렬

        # 최근 NDVI 이미지를 가져오기
        image = ndvi_ic.first()
        if image is not None:
            # 이미지의 날짜 구하기
            info = image.getInfo()
            ndvi_date = datetime.fromtimestamp(info['properties']['system:time_start']/1000, UTC).strftime('%Y-%m-%d')
            ndvi_val = image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=pt,
                scale=250
            ).get('NDVI').getInfo()
            if ndvi_val is not None:
                ndvi = float(ndvi_val) / 10000.0
            else:
                ndvi = None
        else:
            ndvi, ndvi_date = None, None

        if ndvi is not None and ndvi_date is not None:
            ndvi_before_list.append(ndvi)
            ndvi_before_date_list.append(ndvi_date)
            # 산불 발생일 기준 NDVI가 며칠 전 값인지
            days_before = (fire_dt - datetime.strptime(ndvi_date, '%Y-%m-%d')).days
            ndvi_before_days_list.append(days_before)
        else:
            ndvi_before_list.append(None)
            ndvi_before_date_list.append(None)
            ndvi_before_days_list.append(None)

    except Exception as e:
        print(f"NDVI 추출 실패: {lat}, {lng}, {fire_date} - {e}")
        ndvi_before_list.append(None)
        ndvi_before_date_list.append(None)
        ndvi_before_days_list.append(None)

    count += 1
    if count % 100 == 0:
        print(f"[MODIS] {count}개 처리 완료")

# 4. 컬럼 추가 및 저장
df['ndvi_before'] = ndvi_before_list
df['ndvi_before_date'] = ndvi_before_date_list
df['ndvi_before_days'] = ndvi_before_days_list

df.to_csv('fire_with_ndvi_before.csv', index=False, encoding='utf-8-sig')
print(f"NDVI(직전) 추출 완료: {len(df)}건 (fire_with_ndvi_before.csv)")