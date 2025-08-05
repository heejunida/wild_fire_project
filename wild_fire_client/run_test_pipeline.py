

import pandas as pd
import subprocess
import json
import os
import sys
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Constants ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Use the full dataset for the final run
INPUT_FILE = '/tmp/large_fire_sample.csv' 
OUTPUT_FILE = '/tmp/large_fire_features.csv'
PYTHON_EXECUTABLE = '/opt/anaconda3/bin/python'
MAX_WORKERS = 10 # Number of parallel workers

# --- Scripts to run ---
FETCH_WEATHER_SCRIPT = os.path.join(BASE_DIR, 'auto_collection/fetch_all_weather.py')
FETCH_LAND_SCRIPT = os.path.join(BASE_DIR, 'auto_collection/land/fetch_land_merge.py')
FETCH_HGFC_SCRIPT = os.path.join(BASE_DIR, 'auto_collection/forest_data/hgfc.py')
FETCH_NDVI_SCRIPT = os.path.join(BASE_DIR, 'auto_collection/forest_data/ndvi_modis.py')
FEATURE_ENGINEERING_SCRIPT = os.path.join(BASE_DIR, 'auto_collection/feature_engineering.py')

def run_subprocess(command, input_data=None):
    """Helper to run a python script with optional input data."""
    try:
        process = subprocess.run(
            command,
            input=input_data,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        return json.loads(process.stdout)
    except subprocess.CalledProcessError as e:
        return {"error": f"Stderr: {e.stderr}", "success": False}
    except json.JSONDecodeError as e:
        return {"error": f"JSON Decode Error. Stdout: {process.stdout}", "success": False}

def process_single_row(row_tuple):
    """
    Encapsulates all processing for a single row of the dataframe.
    This function will be executed in parallel by threads.
    """
    index, row = row_tuple
    lat = row.get('lat')
    lng = row.get('lng')
    fire_date_str = pd.to_datetime(row.get('fire_date')).strftime('%Y%m%d')
    year = str(row.get('startyear'))
    
    starttime = row.get('starttime', '14:00:00')
    if pd.isna(starttime):
        starttime = '14:00:00'
    fire_time_hour = int(str(starttime).split(':')[0])

    # 1. Fetch Weather Data
    weather_data = run_subprocess([PYTHON_EXECUTABLE, FETCH_WEATHER_SCRIPT, str(lat), str(lng), fire_date_str, str(fire_time_hour)])
    if not weather_data.get("success"):
        print(f"Row {index}: Weather fetch failed. Error: {weather_data.get('error')}", file=sys.stderr)
        return None

    # 2. Fetch Land Data
    land_data = run_subprocess([PYTHON_EXECUTABLE, FETCH_LAND_SCRIPT, str(lat), str(lng)])
    
    # 3. Fetch Forest (HGFC) Data
    hgfc_data = run_subprocess([PYTHON_EXECUTABLE, FETCH_HGFC_SCRIPT, str(lat), str(lng), year])

    # 4. Fetch NDVI Data
    ndvi_data = run_subprocess([PYTHON_EXECUTABLE, FETCH_NDVI_SCRIPT, str(lat), str(lng), row.get('fire_date')])

    # 5. Merge all data
    combined_data = {**row.to_dict(), **weather_data, **land_data, **hgfc_data, **ndvi_data}

    # 6. Feature Engineering
    engineered_data = run_subprocess(
        [PYTHON_EXECUTABLE, FEATURE_ENGINEERING_SCRIPT],
        input_data=json.dumps(combined_data)
    )
    
    if "error" in engineered_data:
        print(f"Row {index}: Feature engineering failed. Error: {engineered_data.get('error')}", file=sys.stderr)
        return None
        
    return engineered_data

def main():
    try:
        df = pd.read_csv(INPUT_FILE)
        # For testing, uncomment the line below
        # df = df.head(20)
    except FileNotFoundError:
        print(f"Input file not found: {INPUT_FILE}", file=sys.stderr)
        return

    all_results = []
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Create a list of tasks
        tasks = {executor.submit(process_single_row, item): item for item in df.iterrows()}
        
        # Process tasks as they complete and show progress bar
        for future in tqdm(as_completed(tasks), total=len(df), desc="Enriching data in parallel"):
            result = future.result()
            if result is not None:
                all_results.append(result)

    # 7. Save final results
    if all_results:
        result_df = pd.DataFrame(all_results)
        result_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        print(f"\nProcessing complete. Enriched data saved to {OUTPUT_FILE}")
        print(f"Successfully processed {len(result_df)} / {len(df)} rows.")
    else:
        print("\nNo data was successfully processed.")

if __name__ == '__main__':
    main()

