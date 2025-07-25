import pandas as pd
import numpy as np
import re

def create_cleaned_dataset(input_file='wild_fire_client/final_merged_feature_engineered.csv', output_file='wild_fire_client/cleaned_ignition_data.csv'):
    """
    Loads the full feature-engineered dataset, removes all columns containing
    post-ignition (future) information, and saves the result to a new CSV file.
    """
    try:
        df = pd.read_csv(input_file, encoding="utf-8")
        print(f"Successfully loaded '{input_file}' with shape: {df.shape}")
    except FileNotFoundError:
        print(f"Error: The input file '{input_file}' was not found. Please ensure it is in the correct directory.")
        return

    # Identify columns that contain information from after the fire started (t > 0).
    # This includes any weather columns with suffixes like _3h, _6h, ..., _171h, etc.
    # It also includes any columns related to the end of the fire.
    
    # Regex to find columns like '_3h', '_6h', ..., '_12h', etc.
    # It looks for an underscore, one or more digits, and the letter 'h'.
    future_weather_pattern = re.compile(r'_\d+h$')
    
    cols_to_drop = []
    for col in df.columns:
        # Check for '_Xh' suffix where X is not 0
        match = future_weather_pattern.search(col)
        if match and not col.endswith('_0h'):
            cols_to_drop.append(col)
            
        # Check for columns related to the end of the fire or the duration
        if 'end' in col or 'duration' in col:
            cols_to_drop.append(col)

    # Also remove non-feature time columns that might remain
    cols_to_drop.extend([col for col in df.columns if col.startswith('dt_')])

    # Ensure we don't accidentally drop essential columns if names are weird
    # This is a safeguard, but our logic should be specific enough.
    cols_to_drop = list(set(cols_to_drop)) # Get unique list of columns to drop

    original_col_count = df.shape[1]
    df_cleaned = df.drop(columns=cols_to_drop, errors='ignore')
    new_col_count = df_cleaned.shape[1]

    print(f"\nIdentified and removed {len(cols_to_drop)} columns containing post-ignition data.")
    print(f"Original number of columns: {original_col_count}")
    print(f"New number of columns: {new_col_count}")

    # Save the cleaned dataframe to a new file
    try:
        df_cleaned.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n✅ Successfully saved cleaned data to '{output_file}'")
    except Exception as e:
        print(f"\nError saving the file: {e}")

if __name__ == '__main__':
    create_cleaned_dataset()
