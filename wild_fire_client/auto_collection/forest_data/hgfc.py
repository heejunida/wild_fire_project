import ee
import sys
import json
from google.oauth2 import service_account

# --- CORRECT AUTHENTICATION FOR SERVERS ---
CREDENTIALS_FILE = '/Users/heejunida/wild_fire_project/ee-credentials.json'
SERVICE_ACCOUNT_EMAIL = 'wildfire@arcane-attic-466102-b2.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(SERVICE_ACCOUNT_EMAIL, key_file=CREDENTIALS_FILE)
ee.Initialize(credentials=credentials, project='arcane-attic-466102-b2')

def get_hanssen_treecover(lat, lng, year, window=5, scale=30):
    try:
        pt = ee.Geometry.Point(float(lng), float(lat))
        offset = (window // 2) * scale
        region = pt.buffer(offset).bounds()

        # Hansen Global Forest Change v1.11 (2000-2023)
        gfc = ee.Image('UMD/hansen/global_forest_change_2023_v1_11')
        
        # Get tree cover for the specified year
        treecover2000 = gfc.select('treecover2000')
        lossyear = gfc.select('lossyear')
        
        loss_mask = lossyear.lte(int(year) - 2000)
        
        treecover_at_year = treecover2000.where(loss_mask, 0)

        stats = treecover_at_year.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=scale,
            maxPixels=1e7
        )
        
        mean_cover = stats.get('treecover2000').getInfo()
        
        return {"treecover_pre_fire_5x5": mean_cover if mean_cover is not None else 0}

    except Exception as e:
        return {"error": f"GEE Tree Cover processing failed: {str(e)}"}

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(json.dumps({"error": "Usage: python hgfc.py lat lng YYYY"}))
        sys.exit(1)
        
    lat_in = float(sys.argv[1])
    lng_in = float(sys.argv[2])
    year_in = sys.argv[3]
    
    result = get_hanssen_treecover(lat_in, lng_in, year_in)
    print(json.dumps(result))