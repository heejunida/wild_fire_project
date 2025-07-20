import ee
import pandas as pd

# 1. Earth Engine 인증 및 초기화
# Make sure you have authenticated and initialized GEE
# If you're running this for the first time or if your token expires,
# you'll need to run ee.Authenticate() and follow the instructions.
# ee.Authenticate() # Uncomment this line if you need to authenticate
ee.Initialize(project='deep-theorem-456805-p2') # Replace with your GEE project ID

# 2. 산불이력 데이터 불러오기
in_csv = "fire_merged_with_ndvi_before.csv"
try:
    df = pd.read_csv(in_csv, encoding='utf-8-sig')
except FileNotFoundError:
    print(f"Error: The input CSV file '{in_csv}' was not found.")
    print("Please ensure 'gangwon_fire_ml_input.csv' is in a 'fire_csv' subdirectory.")
    exit() # Exit if the input file is not found

# Initialize lists to store results
treecover_pre_fire_5x5 = []
treecover_pixel_cnt = []
treecover_used_fireyear = []

# Hansen Global Forest Change dataset (v1.12, updated to 2024)
# 'treecover2000': Tree canopy cover for year 2000 (0-100%).
# 'lossyear': Year of gross forest cover loss event (0 for no loss, 1-24 for 2001-2024).
gfc_image = ee.Image("UMD/hansen/global_forest_change_2024_v1_12")

for idx, row in df.iterrows():
    lat, lng = float(row['lat']), float(row['lng'])
    fire_year = int(row['startyear'])  # 산불 발생 연도

    try:
        point = ee.Geometry.Point(lng, lat)
        # Buffer the point by 250m and get its bounding box (approx. 5x5 pixels at 30m resolution)
        grid = point.buffer(250).bounds()

        # Define a mask for pixels that were forested at or before the fire_year.
        # 'lossyear' is 0 for no loss, or 1-24 for years 2001-2024.
        # So, if lossyear is 0 (no loss), OR (lossyear + 2000) is greater than or equal to fire_year,
        # it means the forest was present at the fire_year.
        # Note: If fire_year is 2000, and lossyear is 0, it means no loss until at least 2024, so it was there in 2000.
        # If fire_year is 2005, and lossyear is 4 (meaning 2004 loss), then (2004 < 2005), so it's lost.
        # If fire_year is 2005, and lossyear is 5 (meaning 2005 loss), then (2005 >= 2005), so it's considered present.
        # If fire_year is 2005, and lossyear is 0, it means no loss until 2024, so it's present in 2005.

        # The condition `(gfc_image.select('lossyear').eq(0))` checks for no loss.
        # The condition `(gfc_image.select('lossyear').add(2000).gte(fire_year))` checks if loss
        # happened at or after the fire year (meaning forest was present up to the fire year).
        forest_present_mask = gfc_image.select('lossyear').eq(0).Or(
            gfc_image.select('lossyear').add(2000).gte(fire_year)
        )

        # Apply the mask to the 'treecover2000' band.
        # Pixels where the mask is false (forest was lost before fire_year) will be masked out (become null).
        treecover_masked = gfc_image.select('treecover2000').updateMask(forest_present_mask)

        # Calculate the mean treecover for the unmasked pixels and count the number of valid (unmasked) pixels.
        # Using combine with sharedInputs=True is efficient as it makes a single pass over the data.
        combined_reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)

        region_stats = treecover_masked.reduceRegion(
            reducer=combined_reducer,
            geometry=grid,
            scale=30,  # Resolution of the Hansen data
            maxPixels=1e8 # Maximum number of pixels to process in the region
        )

        # Get the results from the Earth Engine server
        region_info = region_stats.getInfo()

        # Extract the mean treecover and pixel count. GEE appends '_mean' and '_count' to band names.
        current_treecover = region_info.get('treecover2000_mean')
        current_pixel_count = region_info.get('treecover2000_count')

        # Handle cases where no valid pixels were found (e.g., all were non-forest or lost before fire)
        if current_treecover is not None and current_pixel_count is not None and current_pixel_count > 0:
            treecover_pre_fire_5x5.append(current_treecover)
            treecover_pixel_cnt.append(current_pixel_count)
            print(f"[{idx+1}] {fire_year}년 산불 전 실제 산림률: {lat}, {lng} = {current_treecover:.2f} (n={current_pixel_count})")
        else:
            treecover_pre_fire_5x5.append(None)
            treecover_pixel_cnt.append(0)
            print(f"[{idx+1}] 산불 전 산림률 없음(유효 픽셀 0개): {lat}, {lng}")

    except ee.EEException as ee_err:
        # Catch Earth Engine specific errors
        print(f"[{idx+1}] Earth Engine 오류 발생: {lat}, {lng}, {fire_year} - {ee_err}")
        treecover_pre_fire_5x5.append(None)
        treecover_pixel_cnt.append(0)
    except Exception as e:
        # Catch any other general exceptions
        print(f"[{idx+1}] 일반 오류 발생: {lat}, {lng}, {fire_year} - {e}")
        treecover_pre_fire_5x5.append(None)
        treecover_pixel_cnt.append(0)

    treecover_used_fireyear.append(fire_year)

    if (idx + 1) % 100 == 0:
        print(f"[Hansen 5x5 mean] {idx+1}건 처리 완료")

# 3. 결과 컬럼 추가/저장
df['treecover_pre_fire_5x5'] = treecover_pre_fire_5x5      # 산불 전(실제 존재) 숲 피복률(평균)

out_csv = "fire_with_treecover_pre_fire_5x5.csv"
df.to_csv(out_csv, index=False, encoding='utf-8-sig')
print(f"최종 저장 완료: {out_csv} ({len(df)}건)")