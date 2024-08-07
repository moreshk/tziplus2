import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os

# Read ticker symbols from NSE200.csv
tickerSymbols = pd.read_csv('NSE200.csv', header=None)[0].tolist()

# Read sector information from ind_nifty200list.csv
sector_info = pd.read_csv('ind_nifty200list.csv')

# Add .NS suffix to the symbols in sector_info to match tickerSymbols
sector_info['Symbol'] = sector_info['Symbol'] + '.NS'

# Get today's date and the date 6 months ago
endDate = datetime.now()
startDate = endDate - timedelta(days=90)

# Initialize a dictionary to store performance data
performance_data = {}

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the folder structure
base_folder = os.path.join(script_dir, 'sector_data')
input_folder = os.path.join(base_folder, 'input')
output_folder = os.path.join(base_folder, 'output')

# Create folders if they don't exist
os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

# Fetch price data and calculate performance for each ticker
for ticker in tickerSymbols:
    try:
        # Define the cache file name
        cache_file = f"{input_folder}/{ticker}_{startDate.strftime('%Y%m%d')}_{endDate.strftime('%Y%m%d')}.csv"
        
        # Check if data is already cached
        if os.path.exists(cache_file):
            data = pd.read_csv(cache_file, index_col='Date', parse_dates=True)
        else:
            # Download data
            data = yf.download(ticker, start=startDate, end=endDate)
            if not data.empty:
                data.to_csv(cache_file)
        
        if not data.empty:
            # Calculate performance as percentage change
            start_price = data['Close'].iloc[0]
            end_price = data['Close'].iloc[-1]
            performance = ((end_price - start_price) / start_price) * 100

            # Get the sector for the ticker
            sector = sector_info[sector_info['Symbol'] == ticker]['Industry'].values[0]

            # Get market cap
            ticker_obj = yf.Ticker(ticker)
            market_cap = ticker_obj.info.get('marketCap', 'N/A')

            # Store the performance data
            if sector not in performance_data:
                performance_data[sector] = []
            performance_data[sector].append((ticker, performance, market_cap))
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")

# Calculate weighted average performance for each sector
sector_performance = {}
for sector, performances in performance_data.items():
    total_market_cap = sum([market_cap for _, _, market_cap in performances if market_cap != 'N/A'])
    if total_market_cap > 0:
        weighted_perf = sum([perf * market_cap for _, perf, market_cap in performances if market_cap != 'N/A']) / total_market_cap
        sector_performance[sector] = weighted_perf
    else:
        sector_performance[sector] = sum([perf for _, perf, _ in performances]) / len(performances)

# Prepare data for export
export_data = []
for sector, avg_perf in sorted(sector_performance.items(), key=lambda x: x[1], reverse=True):
    for ticker, perf, market_cap in sorted(performance_data[sector], key=lambda x: x[1], reverse=True):
        export_data.append([sector, ticker, round(perf, 1), market_cap])

# Convert to DataFrame for individual company data
export_df = pd.DataFrame(export_data, columns=['Sector', 'Ticker', 'Performance', 'Market Cap'])

# Export individual company data to CSV
export_df.to_csv(os.path.join(output_folder, 'individual_performance.csv'), index=False)

# Convert to DataFrame for sector performance data
sector_df = pd.DataFrame(sector_performance.items(), columns=['Sector', 'Weighted Performance'])

# Round the weighted performance to 1 decimal place
sector_df['Weighted Performance'] = sector_df['Weighted Performance'].round(1)

# Sort sector performance data in descending order
sector_df = sector_df.sort_values(by='Weighted Performance', ascending=False)

# Export sector performance data to CSV
sector_df.to_csv(os.path.join(output_folder, 'step1_sector_performance.csv'), index=False)

# Output the results
print("Sector Performance:")
for sector, avg_perf in sector_performance.items():
    print(f"{sector}: {avg_perf:.2f}%")
    for ticker, perf, market_cap in performance_data[sector]:
        print(f"  {ticker}: {perf:.2f}%, Market Cap: {market_cap}")