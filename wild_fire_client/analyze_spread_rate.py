import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_spread_rate_distribution(file_path):
    """
    Loads the data, calculates spread rate, and generates a histogram
    to help identify natural breaks for classification.
    """
    try:
        df = pd.read_csv(file_path, encoding="utf-8")

        # Calculate spread rate, handling division by zero
        df_speed = df[df['fire_duration_hours'] > 0].copy()
        df_speed['spread_rate'] = df_speed['fire_area'] / df_speed['fire_duration_hours']

        # --- Visualization ---
        plt.figure(figsize=(14, 6))

        # Plot 1: Full distribution (likely skewed)
        plt.subplot(1, 2, 1)
        sns.histplot(df_speed['spread_rate'], bins=50, kde=False)
        plt.title('Full Distribution of Spread Rate')
        plt.xlabel('Spread Rate (ha/hour)')
        plt.ylabel('Frequency')
        plt.yscale('log') # Use log scale to see the tail

        # Plot 2: Zoomed-in distribution (clipping outliers for clarity)
        quantile_95 = df_speed['spread_rate'].quantile(0.95)
        plt.subplot(1, 2, 2)
        sns.histplot(df_speed[df_speed['spread_rate'] < quantile_95]['spread_rate'], bins=50, kde=True)
        plt.title(f'Distribution of Spread Rate (up to 95th percentile: {quantile_95:.2f} ha/hr)')
        plt.xlabel('Spread Rate (ha/hour)')
        plt.ylabel('Frequency')

        plt.tight_layout()
        # Save the plot to a file
        plot_path = 'spread_rate_distribution.png'
        plt.savefig(plot_path)
        print(f"Plot saved to {plot_path}")


        # --- Print descriptive statistics to help find thresholds ---
        print("\nDescriptive Statistics for Spread Rate (ha/hour):")
        print(df_speed['spread_rate'].describe(percentiles=[.25, .33, .5, .66, .75, .9, .95]))

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    analyze_spread_rate_distribution("final_merged_feature_engineered.csv")
