import pandas as pd
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, 'final_enriched_with_nasa.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, 'final_cleaned_for_modeling.csv')
AREA_CAP = 100
# Based on our analysis, a 7-digit number is unrealistic. We will cap it.
SPREAD_INDEX_CAP = 90000 

# --- Main Cleaning Function ---
def clean_fire_data(input_path, output_path, area_cap, spread_cap):
    """
    Loads the fire dataset, removes rows with extreme fire_area values,
    caps the potential_spread_index to a realistic maximum,
    and saves the cleaned data to a new file.
    """
    print("--- Starting Data Cleaning and Capping Process ---")

    # --- Load Data ---
    try:
        df = pd.read_csv(input_path)
        print(f"✅ Data loaded successfully from {os.path.basename(input_path)}. Initial rows: {len(df)}")
    except FileNotFoundError:
        print(f"❌ Error: Input data file not found at {input_path}")
        return

    # --- Step 1: Remove Outliers based on fire_area ---
    initial_rows = len(df)
    df_cleaned = df[df['fire_area'] <= area_cap].copy()
    rows_removed = initial_rows - len(df_cleaned)
    
    if rows_removed > 0:
        print(f"\nRemoved {rows_removed} rows with fire_area > {area_cap}.")
    else:
        print(f"\nNo outliers found for fire_area > {area_cap}.")

    # --- Step 2: Cap Outliers based on potential_spread_index ---
    if 'potential_spread_index' in df_cleaned.columns:
        # Identify how many values are above the cap
        over_cap_count = (df_cleaned['potential_spread_index'] > spread_cap).sum()
        
        if over_cap_count > 0:
            # Use .loc to safely modify the DataFrame and avoid SettingWithCopyWarning
            df_cleaned.loc[df_cleaned['potential_spread_index'] > spread_cap, 'potential_spread_index'] = spread_cap
            print(f"Capped {over_cap_count} rows where potential_spread_index > {spread_cap}.")
        else:
            print(f"No values needed capping for potential_spread_index > {spread_cap}.")
    else:
        print("⚠️ Warning: 'potential_spread_index' column not found. Skipping capping step.")

    # --- Save Cleaned Data ---
    try:
        df_cleaned.to_csv(output_path, index=False, encoding='utf-8')
        print(f"✅ Cleaned and capped data saved to {os.path.basename(output_path)}. Final rows: {len(df_cleaned)}")
    except Exception as e:
        print(f"❌ Error saving cleaned data file: {e}")

if __name__ == '__main__':
    clean_fire_data(INPUT_FILE, OUTPUT_FILE, AREA_CAP, SPREAD_INDEX_CAP)