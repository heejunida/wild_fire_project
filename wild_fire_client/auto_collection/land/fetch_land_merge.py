import sys
import numpy as np
import ee
import geemap
import json

# GEE 인증/초기화 (서버에서는 1번만 필요, 인증은 직접!)
ee.Initialize(project='deep-theorem-456805-p2')

def get_dem_slope_aspect_stats(lat, lng, window=5, scale=30):
    try:
        offset = (window // 2) * scale
        pt = ee.Geometry.Point(float(lng), float(lat))
        region = pt.buffer(offset).bounds()

        dem = ee.Image("NASA/NASADEM_HGT/001")
        slope = ee.Terrain.slope(dem)
        aspect = ee.Terrain.aspect(dem)

        # Elevation
        elev_stats = dem.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.stdDev(), sharedInputs=True
            ).combine(
                reducer2=ee.Reducer.minMax(), sharedInputs=True
            ),
            geometry=region, scale=scale, maxPixels=1e7
        )
        # Slope
        slope_stats = slope.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.stdDev(), sharedInputs=True
            ).combine(
                reducer2=ee.Reducer.minMax(), sharedInputs=True
            ),
            geometry=region, scale=scale, maxPixels=1e7
        )
        # Aspect (mode, std, north_ratio, south_ratio)
        aspect_img = aspect.clip(region)
        aspect_arr = np.array(
            geemap.ee_to_numpy(aspect_img, region=region, scale=scale).flatten()
        )
        aspect_arr = aspect_arr[~np.isnan(aspect_arr)]
        if aspect_arr.size == 0:
            aspect_mode = None
            aspect_std = None
            north_ratio = None
            south_ratio = None
        else:
            aspect_mode = float(np.bincount(aspect_arr.astype(int)).argmax())
            aspect_std = float(np.std(aspect_arr))
            south_ratio = float(np.sum((aspect_arr >= 135) & (aspect_arr <= 225)) / len(aspect_arr))
            north_ratio = float(np.sum((aspect_arr >= 315) | (aspect_arr <= 45)) / len(aspect_arr))

        res = {
            "elevation_mean": elev_stats.get("elevation_mean").getInfo() if elev_stats.get("elevation_mean") else None,
            "elevation_std": elev_stats.get("elevation_stdDev").getInfo() if elev_stats.get("elevation_stdDev") else None,
            "elevation_min": elev_stats.get("elevation_min").getInfo() if elev_stats.get("elevation_min") else None,
            "elevation_max": elev_stats.get("elevation_max").getInfo() if elev_stats.get("elevation_max") else None,
            "slope_mean": slope_stats.get("slope_mean").getInfo() if slope_stats.get("slope_mean") else None,
            "slope_std": slope_stats.get("slope_stdDev").getInfo() if slope_stats.get("slope_stdDev") else None,
            "slope_min": slope_stats.get("slope_min").getInfo() if slope_stats.get("slope_min") else None,
            "slope_max": slope_stats.get("slope_max").getInfo() if slope_stats.get("slope_max") else None,
            "aspect_mode": aspect_mode,
            "aspect_std": aspect_std,
            "aspect_north_ratio": north_ratio,
            "aspect_south_ratio": south_ratio
        }
        return res
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python fetch_dem.py lat lng"}))
        sys.exit(1)
    lat = float(sys.argv[1])
    lng = float(sys.argv[2])
    result = get_dem_slope_aspect_stats(lat, lng)
    print(json.dumps(result, ensure_ascii=False))