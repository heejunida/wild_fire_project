import pandas as pd
import numpy as np
import ee
import geemap

ee.Authenticate()
ee.Initialize(project='deep-theorem-456805-p2')

df = pd.read_csv("fire_with_treecover_pre_fire_5x5.csv")

def get_dem_slope_aspect_stats(lat, lng, window=5, scale=30):
    try:
        # 5x5 픽셀(약 150m x 150m) 사각형 window
        offset = (window // 2) * scale
        pt = ee.Geometry.Point(float(lng), float(lat))
        region = pt.buffer(offset).bounds()

        dem = ee.Image("NASA/NASADEM_HGT/001")
        slope = ee.Terrain.slope(dem)
        aspect = ee.Terrain.aspect(dem)

        # 1. Elevation stats
        elev_stats = dem.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.stdDev(), sharedInputs=True
            ).combine(
                reducer2=ee.Reducer.minMax(), sharedInputs=True
            ),
            geometry=region, scale=scale, maxPixels=1e7
        )

        # 2. Slope stats
        slope_stats = slope.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.stdDev(), sharedInputs=True
            ).combine(
                reducer2=ee.Reducer.minMax(), sharedInputs=True
            ),
            geometry=region, scale=scale, maxPixels=1e7
        )

        # 3. Aspect window stats (mode, std, north_ratio, south_ratio)
        aspect_img = aspect.clip(region)
        aspect_arr = np.array(
            geemap.ee_to_numpy(aspect_img, region=region, scale=scale).flatten()
        )
        aspect_arr = aspect_arr[~np.isnan(aspect_arr)]
        if aspect_arr.size == 0:
            aspect_mode = np.nan
            aspect_std = np.nan
            north_ratio = np.nan
            south_ratio = np.nan
        else:
            # mode (최빈값)
            aspect_mode = float(pd.Series(aspect_arr).mode().values[0])
            # std (방위의 circular std, 간단히 일반 std로도 충분)
            aspect_std = float(np.std(aspect_arr))
            # 남향(135~225) 비율, 북향(315~360 & 0~45) 비율
            south_ratio = np.sum((aspect_arr >= 135) & (aspect_arr <= 225)) / len(aspect_arr)
            north_ratio = (
                np.sum((aspect_arr >= 315) | (aspect_arr <= 45))
                / len(aspect_arr)
            )
        res = {
            # Elevation
            "elevation_mean": elev_stats.get("elevation_mean").getInfo() if elev_stats.get("elevation_mean") else np.nan,
            "elevation_std": elev_stats.get("elevation_stdDev").getInfo() if elev_stats.get("elevation_stdDev") else np.nan,
            "elevation_min": elev_stats.get("elevation_min").getInfo() if elev_stats.get("elevation_min") else np.nan,
            "elevation_max": elev_stats.get("elevation_max").getInfo() if elev_stats.get("elevation_max") else np.nan,
            # Slope
            "slope_mean": slope_stats.get("slope_mean").getInfo() if slope_stats.get("slope_mean") else np.nan,
            "slope_std": slope_stats.get("slope_stdDev").getInfo() if slope_stats.get("slope_stdDev") else np.nan,
            "slope_min": slope_stats.get("slope_min").getInfo() if slope_stats.get("slope_min") else np.nan,
            "slope_max": slope_stats.get("slope_max").getInfo() if slope_stats.get("slope_max") else np.nan,
            # Aspect
            "aspect_mode": aspect_mode,
            "aspect_std": aspect_std,
            "aspect_north_ratio": north_ratio,
            "aspect_south_ratio": south_ratio
        }
        return res
    except Exception as e:
        print(f"DEM/경사/방위 윈도우 추출 실패: {lat},{lng} → {e}")
        return {k: np.nan for k in [
            "elevation_mean","elevation_std","elevation_min","elevation_max",
            "slope_mean","slope_std","slope_min","slope_max",
            "aspect_mode","aspect_std","aspect_north_ratio","aspect_south_ratio"
        ]}

# 결과 저장용 리스트
dem_list = []
for idx, row in df.iterrows():
    lat = row['lat']
    lng = row['lng']
    stats = get_dem_slope_aspect_stats(lat, lng)
    dem_list.append(stats)
    if idx % 20 == 0:
        print(f"{idx}/{len(df)} DEM/경사/방위 5x5 window 추출중...")

dem_df = pd.DataFrame(dem_list)
result_df = pd.concat([df, dem_df], axis=1)
result_df.to_csv("gangwon_fire_dem_slope_aspect_window.csv", index=False, encoding="utf-8-sig")
print("DEM/경사/방위 (윈도우) 통계 CSV 저장 완료!")