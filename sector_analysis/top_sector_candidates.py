import subprocess
import pandas as pd
import os

# Run sector_performance.py
subprocess.run(["python", "sector_analysis/sector_performance.py"])

# Define the output folder
output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sector_data', 'output')

# Read sector performance data
sector_df = pd.read_csv(os.path.join(output_folder, 'sector_performance.csv'))

# Identify top 6 performing sectors
top_sectors = sector_df.nlargest(15, 'Weighted Performance')['Sector'].tolist()

# Read individual performance data
individual_df = pd.read_csv(os.path.join(output_folder, 'individual_performance.csv'))

# Filter tickers from top sectors with performance > 40%
filtered_df = individual_df[(individual_df['Sector'].isin(top_sectors)) & (individual_df['Performance'] > 25)]

# Select relevant columns
filtered_df = filtered_df[['Ticker', 'Sector', 'Performance']]

# Save the filtered data to a new CSV file
filtered_df.to_csv(os.path.join(output_folder, 'top_sector_candidates.csv'), index=False)

print("Filtered data saved to top_sector_candidates.csv")