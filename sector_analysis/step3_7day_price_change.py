import pandas as pd
import os
import yfinance as yf
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the folder structure
base_folder = os.path.join(script_dir, 'sector_data')
input_folder = os.path.join(base_folder, 'output')
output_folder = os.path.join(base_folder, 'output')
data_folder = os.path.join(base_folder, 'data')

# Create data folder if it doesn't exist
os.makedirs(data_folder, exist_ok=True)

# Read the sector companies data
sector_companies_file = os.path.join(input_folder, 'step2_sector_companies.csv')
sector_companies = pd.read_csv(sector_companies_file)

# Calculate date ranges
end_date = datetime.now()
start_date = end_date - timedelta(days=30)  # Fetch 30 days of data to ensure we have enough

# Function to calculate average daily performance
def calc_avg_performance(data):
    daily_returns = data['Close'].pct_change()
    return daily_returns.mean()

# Initialize results list
results = []

# Process each ticker
for _, row in sector_companies.iterrows():
    ticker = row['Ticker']
    sector = row['Sector']
    
    logging.info(f"Processing {ticker}...")
    
    # Define the file name for storing the data
    file_name = f"{data_folder}/{ticker}_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_1d.csv"
    
    # Check if data is already downloaded
    if os.path.exists(file_name):
        # Load data from CSV file
        stock_data = pd.read_csv(file_name, parse_dates=True, index_col='Date')
    else:
        # Download data if not already downloaded
        stock_data = yf.download(ticker, start=start_date, end=end_date, interval='1d')
        stock_data = stock_data.round(2)
        # Save data to CSV file
        stock_data.to_csv(file_name)
    
    # Ensure the index is in datetime format
    stock_data.index = pd.to_datetime(stock_data.index)
    
    if len(stock_data) < 14:
        logging.warning(f"Insufficient data for {ticker}. Skipping...")
        continue
    
    # Calculate averages
    first_7_avg = calc_avg_performance(stock_data.iloc[-14:-7])
    latest_7_avg = calc_avg_performance(stock_data.iloc[-7:])
    
    # Calculate change in daily average
    change_in_avg = (latest_7_avg - first_7_avg) / abs(first_7_avg) * 100 if first_7_avg != 0 else 0
    
    results.append({
        'Sector': sector,
        'Ticker': ticker,
        'First 7 Day Average': round(first_7_avg, 4),
        'Latest 7 Day Average': round(latest_7_avg, 4),
        'Change in Daily Average %': round(change_in_avg, 4)
    })
    logging.info(f"Processed {ticker} successfully.")

# Create DataFrame from results
if results:
    result_df = pd.DataFrame(results)

    # Sort the result by Change in Daily Average % (descending)
    result_df = result_df.sort_values('Change in Daily Average %', ascending=False)

    # Export the result to CSV
    output_file = os.path.join(output_folder, 'step3_performance_comparison.csv')
    result_df.to_csv(output_file, index=False, float_format='%.4f')

    logging.info(f"Performance comparison has been exported to {output_file}")
else:
    logging.warning("No data was processed successfully. Please check your input data and network connection.")