import pandas as pd
import json
import re

def create_location_json(csv_path, json_path):
    """
    Reads the Gangwon fire data CSV, groups locations by the correct city/county,
    and saves the result as a JSON file for the frontend.
    """
    try:
        df = pd.read_csv(csv_path)
        
        required_cols = ['locsi', 'lat', 'lng']
        if not all(col in df.columns for col in required_cols):
            print(f"Error: Input CSV is missing one of the required columns: {required_cols}")
            return

        # Extract the city/county name
        df['region'] = df['locsi'].str.extract(r'(\S+[시군])')
        df = df.dropna(subset=['region'])

        df['location'] = df['locsi']
        
        # Group by the new 'region' column
        grouped = df.groupby('region')[['lat', 'lng', 'location']].apply(lambda x: x.to_dict('records')).reset_index()
        
        # --- FIX: Handle the correct number of columns ---
        # The result of the groupby is a dataframe with columns: 'region', 0
        # We rename the second column to 'locations'
        grouped.columns = ['region', 'locations']
        
        output_json = dict(zip(grouped['region'], grouped['locations']))

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_json, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully created location JSON file at: {json_path}")

    except FileNotFoundError:
        print(f"Error: The input file was not found at {csv_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    csv_input_path = '/Users/heejunida/wild_fire_project/wild_fire_client/gangwon_fire_ml_input.csv'
    json_output_path = '/Users/heejunida/wild_fire_project/wild_fire_server/web/json/mock_forest_locations_with_coords.json'
    create_location_json(csv_input_path, json_output_path)