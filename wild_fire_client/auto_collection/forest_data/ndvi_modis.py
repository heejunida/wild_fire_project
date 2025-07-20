import sys
import ee
import json
from datetime import datetime, timedelta

# 1. 인증 & 초기화
ee.Initialize(project='deep-theorem-456805-p2')

def fetch_ndvi(lat, lng, fire_date):
    try:
        fire_dt = datetime.strptime(fire_date, '%Y-%m-%d')
        # 30일 전 ~ 1일 전
        start_date = (fire_dt - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = (fire_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        pt = ee.Geometry.Point(float(lng), float(lat))
        ndvi_ic = ee.ImageCollection("MODIS/061/MOD13Q1") \
            .filterDate(start_date, end_date) \
            .filterBounds(pt) \
            .sort('system:time_start', False)
        image = ndvi_ic.first()
        if image is not None:
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
            ndvi = None

        result = {"ndvi_before": ndvi, "lat": lat, "lng": lng, "fire_date": fire_date}
        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        result = {"ndvi_before": None, "error": str(e), "lat": lat, "lng": lng, "fire_date": fire_date}
        print(json.dumps(result, ensure_ascii=False))

# ---- main entrypoint ----
if __name__ == "__main__":
    # sys.argv[1]=lat, [2]=lng, [3]=fire_date
    if len(sys.argv) != 4:
        print(json.dumps({"error": "필수 인자: lat lng fire_date(YYYY-MM-DD)"}))
        sys.exit(1)
    lat, lng, fire_date = sys.argv[1], sys.argv[2], sys.argv[3]
    fetch_ndvi(lat, lng, fire_date)