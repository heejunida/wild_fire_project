import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'final_enriched_with_nasa.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'eda_analysis_plots')

# --- Main Analysis Function ---
def perform_eda(file_path):
    """
    Performs Exploratory Data Analysis on the provided dataset.
    """
    print(f"--- Starting EDA for {os.path.basename(file_path)} ---")

    # --- Load Data ---
    try:
        df = pd.read_csv(file_path)
        print("✅ Data loaded successfully.")
    except FileNotFoundError:
        print(f"❌ Error: Data file not found at {file_path}")
        return

    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"✅ Created output directory: {OUTPUT_DIR}")

    # --- 1. Descriptive Statistics ---
    print("\n--- Descriptive Statistics ---")
    # Increase display width to prevent wrapping
    pd.set_option('display.width', 120)
    stats = df.describe()
    print(stats)
    stats.to_csv(os.path.join(OUTPUT_DIR, 'descriptive_statistics.csv'))
    print("\n✅ Full descriptive statistics saved to 'descriptive_statistics.csv'")

    # --- 2. Target Variable Analysis: 'fire_area' ---
    print("\n--- Analyzing Target Variable: 'fire_area' ---")
    plt.figure(figsize=(12, 6))
    sns.histplot(df['fire_area'], bins=50, kde=True)
    plt.title('Distribution of Fire Area (ha)')
    plt.xlabel('Fire Area (ha)')
    plt.ylabel('Frequency')
    plt.savefig(os.path.join(OUTPUT_DIR, 'fire_area_distribution.png'))
    plt.close()
    print("✅ Saved 'fire_area_distribution.png'")

    # Log-transformed distribution
    df['fire_area_log'] = np.log1p(df['fire_area'])
    plt.figure(figsize=(12, 6))
    sns.histplot(df['fire_area_log'], bins=50, kde=True)
    plt.title('Distribution of Log-Transformed Fire Area (log1p)')
    plt.xlabel('log(1 + Fire Area)')
    plt.ylabel('Frequency')
    plt.savefig(os.path.join(OUTPUT_DIR, 'fire_area_log_distribution.png'))
    plt.close()
    print("✅ Saved 'fire_area_log_distribution.png'")

    # --- 3. Key Feature Analysis (Box Plots for Outliers) ---
    print("\n--- Analyzing Key Features for Outliers ---")
    # Based on the feature importance list from the last run
    key_features = [
        'dry_windy_combo',
        'potential_spread_index',
        'fuel_combo',
        'hot_dry_combo',
        'treecover_pre_fire_5x5',
        't2m_mean_past_24h',
        'rh2m_mean_past_24h'
    ]
    
    for feature in key_features:
        if feature in df.columns:
            plt.figure(figsize=(10, 6))
            sns.boxplot(x=df[feature])
            plt.title(f'Box Plot of {feature}')
            plt.xlabel(feature)
            plt.savefig(os.path.join(OUTPUT_DIR, f'boxplot_{feature}.png'))
            plt.close()
            print(f"✅ Saved 'boxplot_{feature}.png'")
        else:
            print(f"⚠️ Warning: Feature '{feature}' not found in DataFrame.")

    print("\n--- EDA Complete ---")
    print(f"All plots and statistics have been saved to the '{OUTPUT_DIR}' directory.")

if __name__ == '__main__':
    perform_eda(DATA_FILE)
