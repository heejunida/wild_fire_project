import datetime
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np
import sys # Add sys module to get the current python executable

# --- Constants ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
PYTHON_EXECUTABLE = sys.executable # Use the current python executable

# --- Helper Functions for running scripts ---
def run_script(script_name, *args):
    """Constructs path and runs a python script, returning its JSON output."""
    script_path = os.path.join(CLIENT_DIR, script_name)
    command = [PYTHON_EXECUTABLE, script_path] + [str(arg) for arg in args]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=CLIENT_DIR)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running script {script_name} with args {args}.")
        print(f"Stderr: {e.stderr}")
        raise
    except json.JSONDecodeError:
        print(f"Error decoding JSON from script {script_name}.")
        print(f"Stdout: {result.stdout}")
        raise

def run_script_with_json(script_name, json_data):
    """Runs a python script with JSON input via stdin, returning its JSON output."""
    script_path = os.path.join(CLIENT_DIR, script_name)
    command = [PYTHON_EXECUTABLE, script_path]
    try:
        process = subprocess.run(command, input=json.dumps(json_data), capture_output=True, text=True, check=True, cwd=CLIENT_DIR)
        return json.loads(process.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running script {script_name} with JSON.")
        print(f"Stderr: {e.stderr}")
        raise
    except json.JSONDecodeError:
        print(f"Error decoding JSON from script {script_name}.")
        print(f"Stdout: {process.stdout}")
        raise

# --- Performance Metrics ---
_performance_metrics = None
def load_performance_metrics_once():
    global _performance_metrics
    if _performance_metrics is not None: return _performance_metrics
    try:
        csv_path = os.path.join(CLIENT_DIR, "model_performance_summary.csv")
        df = pd.read_csv(csv_path)
        metrics_dict = {}
        for _, row in df.iterrows():
            model_name = row['model_name']
            metrics = row.drop('model_name').to_dict()
            for k, v in metrics.items():
                if isinstance(v, np.generic): metrics[k] = v.item()
            metrics_dict[model_name] = metrics
        _performance_metrics = metrics_dict
        print("✅ Performance metrics loaded.")
    except Exception as e:
        print(f"⚠️ Could not load performance metrics: {e}")
        _performance_metrics = {}
    return _performance_metrics

def replace_nan_with_none(obj):
    """Recursively traverses a data structure and replaces numpy NaN with None."""
    if isinstance(obj, dict):
        return {k: replace_nan_with_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_nan_with_none(elem) for elem in obj]
    elif isinstance(obj, (np.floating, float)) and np.isnan(obj):
        return None
    return obj

# --- Main Pipeline Function ---
def run_feature_pipeline(lat, lng, fire_date_str, fire_time_str):
    """
    Runs the entire data collection and feature engineering pipeline by calling
    the original script files using subprocesses.
    """
    fire_date_dt = datetime.datetime.strptime(fire_date_str, '%Y-%m-%d')
    fire_date_for_script = fire_date_dt.strftime('%Y%m%d')
    fire_year = str(fire_date_dt.year)
    fire_hour = fire_time_str.split(':')[0]

    raw_features = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        weather_future = executor.submit(run_script, "auto_collection/fetch_all_weather.py", lat, lng, fire_date_for_script, fire_hour)
        dem_lc_future = executor.submit(run_script, "auto_collection/land/fetch_land_merge.py", lat, lng)
        ndvi_future = executor.submit(run_script, "auto_collection/forest_data/ndvi_modis.py", lat, lng, fire_date_for_script)
        tree_cover_future = executor.submit(run_script, "auto_collection/forest_data/hgfc.py", lat, lng, fire_year)
        
        raw_features.update(weather_future.result())
        raw_features.update(dem_lc_future.result())
        raw_features.update(ndvi_future.result())
        raw_features.update(tree_cover_future.result())

    engineered_features = run_script_with_json("auto_collection/feature_engineering.py", raw_features)
    final_prediction = run_script_with_json("predict_all.py", engineered_features)
    
    final_prediction['performance_metrics'] = load_performance_metrics_once()
    
    # FIX: Sanitize the final JSON output to replace NaN with null
    sanitized_prediction = replace_nan_with_none(final_prediction)
    
    return engineered_features, sanitized_prediction
