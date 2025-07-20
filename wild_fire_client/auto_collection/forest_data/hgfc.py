import sys
import ee
import json

# 1. GEE 인증 및 초기화 (최초 1회 인증 필요)
ee.Initialize(project='deep-theorem-456805-p2')

def get_treecover_pre_fire(lat, lng, fire_year, window=5, scale=30):
    try:
        lat = float(lat)
        lng = float(lng)
        fire_year = int(fire_year)

        # 중심점에서 5x5 픽셀(약 150m x 150m) window
        offset = (window // 2) * scale  # 예: 2*30=60m
        pt = ee.Geometry.Point(lng, lat)
        grid = pt.buffer(offset).bounds()

        # Hansen Global Forest Change dataset (v1.12, 2024)
        gfc_image = ee.Image("UMD/hansen/global_forest_change_2024_v1_12")

        # 1. 해당 화재 발생년도 시점의 “실제 숲 존재여부” mask
        forest_present_mask = gfc_image.select('lossyear').eq(0).Or(
            gfc_image.select('lossyear').add(2000).gte(fire_year)
        )
        # 2. mask 적용 후 window 내 평균 산림률
        treecover_masked = gfc_image.select('treecover2000').updateMask(forest_present_mask)
        combined_reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)
        region_stats = treecover_masked.reduceRegion(
            reducer=combined_reducer,
            geometry=grid,
            scale=scale,
            maxPixels=1e8
        ).getInfo()

        current_treecover = region_stats.get('treecover2000_mean')
        current_pixel_count = region_stats.get('treecover2000_count')

        result = {
            "treecover_pre_fire_5x5": float(current_treecover) if current_treecover is not None else None,
            "treecover_pixel_count": int(current_pixel_count) if current_pixel_count is not None else 0,
            "window_m": scale * window,
            "fire_year": fire_year
        }
        return result
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(json.dumps({"error": "Usage: python fetch_treecover.py lat lng fire_year"}))
        sys.exit(1)
    lat = sys.argv[1]
    lng = sys.argv[2]
    fire_year = sys.argv[3]  # 반드시 YYYY형식(예: 2021)
    result = get_treecover_pre_fire(lat, lng, fire_year)
    print(json.dumps(result, ensure_ascii=False))