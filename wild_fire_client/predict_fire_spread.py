import pandas as pd
import numpy as np
import joblib
import json
import argparse
from geopy.distance import geodesic
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')
warnings.filterwarnings('ignore', category=FutureWarning)

def create_placeholder_features(lat, lon):
    """
    Creates a single-row DataFrame with placeholder features for prediction.
    
    This is a CRITICAL placeholder. For a real application, this function
    MUST be replaced with one that fetches real-time data (weather, FWI,
    terrain, etc.) for the given lat/lon.
    """
    print("--> Creating placeholder features for prediction.")
    
    # Load the feature lists that the models were trained on
    with open('area_model_columns.json', 'r') as f:
        area_cols = json.load(f)
    with open('speed_model_columns.json', 'r') as f:
        speed_cols = json.load(f)
    
    # Combine all required features, ensuring no duplicates
    all_required_cols = sorted(list(set(area_cols + speed_cols)))
    
    # Create a dictionary with placeholder values.
    # Using median values from a typical dataset might be a reasonable start.
    placeholder_data = {
        'total_precip_7d_start': [10.0], 'dry_days_7d_start': [3.0],
        'total_precip_14d_start': [20.0], 'dry_days_14d_start': [6.0],
        'total_precip_30d_start': [50.0], 'dry_days_30d_start': [10.0],
        'total_precip_60d_start': [100.0], 'dry_days_60d_start': [15.0],
        'total_precip_90d_start': [150.0], 'dry_days_90d_start': [20.0],
        'consecutive_dry_days_start': [5.0], 'T2M_0h': [15.0], 'RH2M_0h': [50.0],
        'WS2M_0h': [2.0], 'WS10M_0h': [3.0], 'PRECTOTCORR_0h': [0.0],
        'PS_0h': [101.0], 'ALLSKY_SFC_SW_DWN_0h': [150.0],
        'ndvi_before': [0.6], 'treecover_pre_fire_5x5': [70.0],
        'elevation_mean': [300.0], 'elevation_std': [50.0], 'elevation_min': [250.0],
        'elevation_max': [350.0], 'slope_mean': [10.0], 'slope_std': [5.0],
        'slope_min': [5.0], 'slope_max': [15.0], 'aspect_mode': [180.0],
        'aspect_std': [30.0], 'aspect_north_ratio': [0.2], 'aspect_south_ratio': [0.3],
        'fire_month': [7.0], 'is_spring': [0.0], 'is_autumn': [0.0],
        'FFMC_0h': [85.0], 'DMC_0h': [40.0], 'DC_0h': [300.0], 'ISI_0h': [8.0],
        'BUI_0h': [50.0], 'FWI_0h': [20.0], 'FFMC_mean_0_12h': [85.0],
        'DMC_mean_0_12h': [40.0], 'DC_mean_0_12h': [300.0], 'ISI_mean_0_12h': [8.0],
        'BUI_mean_0_12h': [50.0], 'FWI_mean_0_12h': [20.0],
        'dry_windy_combo': [15.0], 'hot_dry_combo': [750.0], 'fuel_combo': [120.0],
        'slope_south_combo': [3.0], 'potential_spread_index': [10.0],
        'terrain_var_effect': [2500.0], 'south_steep_effect': [4.5],
        'WS10M_std_0_12h': [1.0], 'T2M_std_0_12h': [2.0], 'RH2M_std_0_12h': [10.0],
        'WD10M_std_0_12h': [20.0], 'max_wind_0_12h': [4.0], 'min_humidity_0_12h': [40.0],
        'max_temp_0_12h': [18.0], 'WD10M_var_0_12h': [400.0], 'wind_steady_flag': [0.0],
        'dry_to_rain_ratio_30d': [0.2], 'ndvi_stress': [0.1], 'high_wind_flag': [0.0],
        'low_humidity_flag': [0.0], 'extreme_hot_flag': [0.0],
        # --- Crucial: Add a placeholder for wind direction ---
        'WD10M_0h': [270.0] # Placeholder: Wind from the West
    }

    # Create a DataFrame from the placeholder data
    features_df = pd.DataFrame(placeholder_data)

    # Ensure all required columns are present, adding any missing ones with a default value (e.g., 0)
    for col in all_required_cols:
        if col not in features_df.columns:
            features_df[col] = 0
            
    # Return the single-row DataFrame with columns in the correct order
    return features_df[all_required_cols]


def predict_area(features, model):
    """Predicts fire area using the loaded XGBoost model."""
    print("--> Predicting fire area...")
    # Ensure columns are in the same order as during training
    with open('area_model_columns.json', 'r') as f:
        model_cols = json.load(f)
    
    # Predict on the log-transformed scale
    predicted_area_log = model.predict(features[model_cols])
    # Inverse transform to get the actual area in hectares
    predicted_area_ha = np.expm1(predicted_area_log)
    
    return predicted_area_ha[0]

def create_geojson_polygon(center_lat, center_lon, radius_m, direction_deg):
    """
    Creates a GeoJSON FeatureCollection with a single elliptical polygon.
    """
    print(f"--> Creating GeoJSON: center=({center_lat}, {center_lon}), radius={radius_m}m, direction={direction_deg}deg")
    
    center_point = (center_lat, center_lon)
    num_points = 32 
    
    # Create a list of coordinates for the polygon
    coordinates = []
    for i in range(num_points):
        angle = i * (360 / num_points)
        # Simple approximation of an ellipse based on wind direction
        # This can be made more sophisticated
        if 90 < direction_deg < 270: # Wind blowing East
             # Elongate more in the direction of the wind
            if abs(angle - direction_deg) < 45 or abs(angle - direction_deg) > 315:
                effective_radius = radius_m * 1.5 
            else:
                effective_radius = radius_m * 0.7
        else: # Wind blowing West
            if abs(angle - direction_deg) < 45 or abs(angle - direction_deg) > 315:
                effective_radius = radius_m * 0.7
            else:
                effective_radius = radius_m * 1.5

        # Calculate the destination point
        destination = geodesic(meters=effective_radius).destination(center_point, angle)
        coordinates.append([destination.longitude, destination.latitude])
    
    # Close the polygon
    coordinates.append(coordinates[0])

    # Create the GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coordinates]
                },
                "properties": {
                    "predicted_area_ha": radius_m**2 * np.pi / 10000, # Re-calculate for properties
                    "wind_direction_deg": direction_deg
                }
            }
        ]
    }
    return json.dumps(geojson, indent=4)

def main(lat, lon):
    """
    Main prediction pipeline.
    """
    try:
        # 1. Load Models
        print("--- Loading models ---")
        area_model = joblib.load('area_regressor_model.joblib')
        
        # 2. Get Features (using placeholder function)
        features = create_placeholder_features(lat, lon)
        
        # 3. Predict Fire Area
        predicted_area = predict_area(features, area_model)
        
        # 4. Calculate radius and get wind direction
        # Radius in meters from area in hectares
        predicted_radius_m = np.sqrt(predicted_area * 10000 / np.pi) 
        wind_direction = features['WD10M_0h'].iloc[0]
        
        print(f"\n--- Prediction Results ---")
        print(f"Predicted Area: {predicted_area:.2f} ha")
        print(f"Resulting Radius: {predicted_radius_m:.2f} m")
        print(f"Assumed Wind Direction: {wind_direction} degrees")

        # 5. Generate GeoJSON
        geojson_output = create_geojson_polygon(lat, lon, predicted_radius_m, wind_direction)
        
        # 6. Print GeoJSON for the Java servlet
        print("\n--- GeoJSON Output ---")
        print(geojson_output)

    except FileNotFoundError as e:
        print(json.dumps({"error": f"Model file not found. Please run the training script first. Details: {e}"}))
    except Exception as e:
        print(json.dumps({"error": f"An error occurred during prediction: {e}"}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Wildfire Spread Prediction")
    parser.add_argument("--lat", type=float, required=True, help="Latitude of the fire's starting point.")
    parser.add_argument("--lon", type=float, required=True, help="Longitude of the fire's starting point.")
    
    args = parser.parse_args()
    
    main(args.lat, args.lon)