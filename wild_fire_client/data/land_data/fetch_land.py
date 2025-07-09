import pandas as pd
import geemap
import ee

ee.Authenticate()
ee.Initialize(project='deep-theorem-456805-p2')

df = pd.read_csv("gangwon_fire_ml_input.csv")  # 네 입력 파일

def get_dem_slope_aspect(lat, lng):
    try:
        pt = ee.Geometry.Point(float(lng), float(lat))
        dem = ee.Image("NASA/NASADEM_HGT/001")
        slope = ee.Terrain.slope(dem)
        aspect = ee.Terrain.aspect(dem)
        # 고도
        elevation = dem.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=pt,
            scale=30
        ).get('elevation').getInfo()
        # 경사
        slope_val = slope.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=pt,
            scale=30
        ).get('slope').getInfo()
        # 방위각
        aspect_val = aspect.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=pt,
            scale=30
        ).get('aspect').getInfo()
        return elevation, slope_val, aspect_val
    except Exception as e:
        print(f"DEM/경사/방위 추출 실패: {lat},{lng} → {e}")
        return None, None, None

elevation_list = []
slope_list = []
aspect_list = []

for idx, row in df.iterrows():
    lat = row['lat']
    lng = row['lng']
    elevation, slope, aspect = get_dem_slope_aspect(lat, lng)
    elevation_list.append(elevation)
    slope_list.append(slope)
    aspect_list.append(aspect)
    if idx % 20 == 0:
        print(f"{idx}/{len(df)} DEM/경사/방위 추출중...")

df['elevation'] = elevation_list
df['slope'] = slope_list
df['aspect'] = aspect_list

df.to_csv("gangwon_fire_dem_slope_aspect.csv", index=False, encoding="utf-8-sig")
print("DEM(고도), Slope(경사), Aspect(방위) CSV 저장 완료!")