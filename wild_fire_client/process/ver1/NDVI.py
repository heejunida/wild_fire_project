import ee
import pandas as pd
import datetime

ee.Authenticate()
ee.Initialize(project='deep-theorem-456805-p2')

df = pd.read_csv("gangwon_fire_ml_input.csv")

def get_ndvi(lat, lng, date, window_days=7):
    point = ee.Geometry.Point(float(lng), float(lat))
    start = (datetime.datetime.strptime(date, "%Y-%m-%d") - datetime.timedelta(days=window_days)).strftime("%Y-%m-%d")
    end = (datetime.datetime.strptime(date, "%Y-%m-%d") + datetime.timedelta(days=window_days)).strftime("%Y-%m-%d")
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterBounds(point) \
        .filterDate(start, end) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
        .sort('CLOUDY_PIXEL_PERCENTAGE')
    image = s2.first()
    if image is None:
        return None
    ndvi = image.normalizedDifference(['B8', 'B4']).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=10,
        maxPixels=1e9
    ).get('nd')
    return ndvi.getInfo() if ndvi else None

ndvi_list = []
count = 0
for idx, row in df.iterrows():
    lat = row['lat']
    lng = row['lng']
    date = row['fire_date']
    dt = datetime.datetime.strptime(date, "%Y-%m-%d")
    if dt < datetime.datetime(2015, 6, 23):
        ndvi = None
    else:
        try:
            ndvi = get_ndvi(lat, lng, date)
        except Exception as e:
            ndvi = None
            print(f"NDVI 추출 실패: {lat}, {lng}, {date} - {e}")
    ndvi_list.append(ndvi)
    count += 1
    if count % 100 == 0:
        print(f"[Sentinel-2] {count}개 처리 완료")

df['ndvi'] = ndvi_list
df.to_csv("fire_with_ndvi_sentinel.csv", index=False, encoding="utf-8-sig")
print("Sentinel-2 완료! fire_with_ndvi_sentinel.csv 파일을 확인하세요.")