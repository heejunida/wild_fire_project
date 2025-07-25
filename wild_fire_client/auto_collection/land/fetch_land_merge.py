import sys
import numpy as np
import ee
import geemap
import json
from google.oauth2 import service_account

# --- CORRECT AUTHENTICATION FOR SERVERS ---
try:
    CREDENTIALS_FILE = '/Users/heejunida/wild_fire_project/ee-credentials.json'
    SERVICE_ACCOUNT_EMAIL = 'wildfire@arcane-attic-466102-b2.iam.gserviceaccount.com'
    credentials = ee.ServiceAccountCredentials(SERVICE_ACCOUNT_EMAIL, key_file=CREDENTIALS_FILE)
    ee.Initialize(credentials=credentials, project='arcane-attic-466102-b2')
except Exception as e:
    print(json.dumps({"error": f"GEE Initialization Failed: {e}"}))
    sys.exit(1)

# IGBP Land Cover Classification Legend
IGBP_LEGEND = {
    1: "Evergreen Needleleaf Forests", 2: "Evergreen Broadleaf Forests",
    3: "Deciduous Needleleaf Forests", 4: "Deciduous Broadleaf Forests",
    5: "Mixed Forests", 6: "Closed Shrublands", 7: "Open Shrublands",
    8: "Woody Savannas", 9: "Savannas", 10: "Grasslands",
    11: "Permanent Wetlands", 12: "Croplands", 13: "Urban and Built-up Lands",
    14: "Cropland/Natural Vegetation Mosaics", 15: "Snow and Ice",
    16: "Barren", 17: "Water Bodies"
}

def get_dem_slope_aspect_stats(lat, lng, window=5, scale=30):
    """Fetches DEM, slope, and aspect statistics."""
    try:
        offset = (window // 2) * scale
        pt = ee.Geometry.Point(float(lng), float(lat))
        region = pt.buffer(offset).bounds()

        dem = ee.Image("NASA/NASADEM_HGT/001")
        slope = ee.Terrain.slope(dem)
        aspect = ee.Terrain.aspect(dem)

        reducers = ee.Reducer.mean().combine(
            reducer2=ee.Reducer.stdDev(), sharedInputs=True
        ).combine(
            reducer2=ee.Reducer.minMax(), sharedInputs=True
        )

        elev_stats = dem.reduceRegion(reducer=reducers, geometry=region, scale=scale, maxPixels=1e7).getInfo()
        slope_stats = slope.reduceRegion(reducer=reducers, geometry=region, scale=scale, maxPixels=1e7).getInfo()

        aspect_arr = np.array(geemap.ee_to_numpy(aspect.clip(region), region=region, scale=scale).flatten())
        aspect_arr = aspect_arr[~np.isnan(aspect_arr)]
        
        if aspect_arr.size == 0:
            aspect_mode, aspect_std, north_ratio, south_ratio = None, None, None, None
        else:
            aspect_mode = float(np.bincount(aspect_arr.astype(int)).argmax())
            aspect_std = float(np.std(aspect_arr))
            south_ratio = float(np.sum((aspect_arr >= 135) & (aspect_arr <= 225)) / len(aspect_arr))
            north_ratio = float(np.sum((aspect_arr >= 315) | (aspect_arr <= 45)) / len(aspect_arr))

        return {
            "elevation_mean": elev_stats.get("elevation_mean"), "elevation_std": elev_stats.get("elevation_stdDev"),
            "elevation_min": elev_stats.get("elevation_min"), "elevation_max": elev_stats.get("elevation_max"),
            "slope_mean": slope_stats.get("slope_mean"), "slope_std": slope_stats.get("slope_stdDev"),
            "slope_min": slope_stats.get("slope_min"), "slope_max": slope_stats.get("slope_max"),
            "aspect_mode": aspect_mode, "aspect_std": aspect_std,
            "aspect_north_ratio": north_ratio, "aspect_south_ratio": south_ratio
        }
    except Exception as e:
        return {"error_dem": f"DEM processing failed: {str(e)}"}

def get_land_cover(lat, lng):
    """Fetches the land cover type."""
    try:
        point = ee.Geometry.Point(float(lng), float(lat))
        land_cover_collection = ee.ImageCollection('MODIS/006/MCD12Q1').select('LC_Type1')
        latest_land_cover = land_cover_collection.sort('system:time_start', False).first()
        land_cover_info = latest_land_cover.sample(point, scale=1).first().getInfo()
        
        if 'properties' in land_cover_info and 'LC_Type1' in land_cover_info['properties']:
            cover_value = land_cover_info['properties']['LC_Type1']
            return {
                "land_cover_code": cover_value,
                "land_cover_name": IGBP_LEGEND.get(cover_value, "Unknown")
            }
        else:
            return {"error_landcover": "Could not extract land cover value."}
    except Exception as e:
        return {"error_landcover": f"Land cover processing failed: {str(e)}"}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python fetch_land_merge.py lat lng"}))
        sys.exit(1)
        
    lat_arg = float(sys.argv[1])
    lng_arg = float(sys.argv[2])
    
    # --- MERGE RESULTS FROM ALL FUNCTIONS ---
    dem_results = get_dem_slope_aspect_stats(lat_arg, lng_arg)
    land_cover_results = get_land_cover(lat_arg, lng_arg)
    
    merged_results = {}
    merged_results.update(dem_results)
    merged_results.update(land_cover_results)
    
    # Check for errors and print final JSON
    if "error_dem" in merged_results or "error_landcover" in merged_results:
        # If there's an error, the JSON will contain the error key and message
        pass
    
    print(json.dumps(merged_results, ensure_ascii=False))
