import sys
import numpy as np
import ee
import geemap
import json
from google.oauth2 import service_account

# --- CORRECT AUTHENTICATION FOR SERVERS ---
CREDENTIALS_FILE = '/Users/heejunida/wild_fire_project/ee-credentials.json'
SERVICE_ACCOUNT_EMAIL = 'wildfire@arcane-attic-466102-b2.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(SERVICE_ACCOUNT_EMAIL, key_file=CREDENTIALS_FILE)
ee.Initialize(credentials=credentials, project='arcane-attic-466102-b2')

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
        ).getInfo()
        # Slope
        slope_stats = slope.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.stdDev(), sharedInputs=True
            ).combine(
                reducer2=ee.Reducer.minMax(), sharedInputs=True
            ),
            geometry=region, scale=scale, maxPixels=1e7
        ).getInfo()
        # Aspect
        aspect_img = aspect.clip(region)
        aspect_arr = np.array(
            geemap.ee_to_numpy(aspect_img, region=region, scale=scale).flatten()
        )
        aspect_arr = aspect_arr[~np.isnan(aspect_arr)]
        if aspect_arr.size == 0:
            aspect_mode, aspect_std, north_ratio, south_ratio = None, None, None, None
        else:
            aspect_mode = float(np.bincount(aspect_arr.astype(int)).argmax())
            aspect_std = float(np.std(aspect_arr))
            south_ratio = float(np.sum((aspect_arr >= 135) & (aspect_arr <= 225)) / len(aspect_arr))
            north_ratio = float(np.sum((aspect_arr >= 315) | (aspect_arr <= 45)) / len(aspect_arr))

        res = {
            "elevation_mean": elev_stats.get("elevation_mean"),
            "elevation_std": elev_stats.get("elevation_stdDev"),
            "elevation_min": elev_stats.get("elevation_min"),
            "elevation_max": elev_stats.get("elevation_max"),
            "slope_mean": slope_stats.get("slope_mean"),
            "slope_std": slope_stats.get("slope_stdDev"),
            "slope_min": slope_stats.get("slope_min"),
            "slope_max": slope_stats.get("slope_max"),
            "aspect_mode": aspect_mode,
            "aspect_std": aspect_std,
            "aspect_north_ratio": north_ratio,
            "aspect_south_ratio": south_ratio
        }
        return res
    except Exception as e:
        return {"error": f"GEE processing failed: {str(e)}"}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python fetch_dem.py lat lng"}))
        sys.exit(1)
    lat = float(sys.argv[1])
    lng = float(sys.argv[2])
    result = get_dem_slope_aspect_stats(lat, lng)
    print(json.dumps(result, ensure_ascii=False))
