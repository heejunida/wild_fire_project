import ee
import sys
import json
from google.oauth2 import service_account

# --- CORRECT AUTHENTICATION FOR SERVERS ---
CREDENTIALS_FILE = '/Users/heejunida/wild_fire_project/ee-credentials.json'
SERVICE_ACCOUNT_EMAIL = 'wildfire@arcane-attic-466102-b2.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(SERVICE_ACCOUNT_EMAIL, key_file=CREDENTIALS_FILE)
ee.Initialize(credentials=credentials, project='arcane-attic-466102-b2')

def get_modis_ndvi_value(lat, lng, date_str):
    try:
        date = ee.Date(date_str)
        pt = ee.Geometry.Point(float(lng), float(lat))
        
        modis_ndvi = ee.ImageCollection('MODIS/061/MOD13A2').filterDate(
            date.advance(-1, 'month'), date.advance(1, 'month')
        ).select('NDVI').mean()

        scale = 1000  # MODIS 1km resolution
        ndvi_value = modis_ndvi.sample(pt, scale).first().get('NDVI').getInfo()
        
        # MODIS NDVI is scaled by 10000
        return {"ndvi_before": ndvi_value * 0.0001 if ndvi_value is not None else None}
        
    except Exception as e:
        # Return a structured error if GEE fails
        return {"error": f"GEE NDVI processing failed: {str(e)}"}

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(json.dumps({"error": "Usage: python ndvi_modis.py lat lng YYYY-MM-DD"}))
        sys.exit(1)
        
    lat_in = float(sys.argv[1])
    lng_in = float(sys.argv[2])
    date_in = sys.argv[3]
    
    result = get_modis_ndvi_value(lat_in, lng_in, date_in)
    print(json.dumps(result))