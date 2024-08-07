import pandas as pd
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the folder structure
base_folder = os.path.join(script_dir, 'sector_data')
input_folder = os.path.join(base_folder, 'output')
output_folder = os.path.join(base_folder, 'output')

# Read the sector performance data
sector_performance_file = os.path.join(input_folder, 'step1_sector_performance.csv')
sector_performance = pd.read_csv(sector_performance_file)

# Get the top 5 performing sectors
top_5_sectors = sector_performance.nlargest(5, 'Weighted Performance')['Sector'].tolist()

# Read the individual performance data
individual_performance_file = os.path.join(input_folder, 'individual_performance.csv')
individual_performance = pd.read_csv(individual_performance_file)

# Filter the data for the top 5 sectors
top_5_sector_companies = individual_performance[individual_performance['Sector'].isin(top_5_sectors)]

# Select only the Sector and Ticker columns
result = top_5_sector_companies[['Sector', 'Ticker']]

# Sort the result by Sector and then by Ticker
result = result.sort_values(['Sector', 'Ticker'])

# Export the result to CSV
output_file = os.path.join(output_folder, 'step2_sector_companies.csv')
result.to_csv(output_file, index=False)

print(f"Top 5 sectors and their companies have been exported to {output_file}")