from datetime import datetime, timedelta
# from plot_chart import plot_chart
import yfinance as yf
import pandas as pd
# from utils import calculate_body_and_shadow, identify_fvg, identify_major_highs_lows, identify_bos, identify_demand_zones, identify_supply_zones, find_closest_zones
import os
import logging
import sys

# Determine the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the project root to the system path
sys.path.append(project_root)

# Import modules from the project root
from plot_chart import plot_chart
from utils import calculate_split_lines,calculate_body_and_shadow, identify_fvg, identify_major_highs_lows, identify_bos, identify_demand_zones, identify_supply_zones, find_closest_zones


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Read ticker symbols from CSV file
csv_file_path = 'sector_analysis/sector_data/output/volatile_with_demand_supply_bottom_2.csv'  # Updated path
ticker_data_df = pd.read_csv(csv_file_path)
tickerSymbols = ticker_data_df['Ticker'].tolist()


# Define the interval (e.g., '1d' for daily, '1h' for hourly, '30m' for 30 minutes)
interval = '15m'  # Change this to your desired interval <----------------------------------------

# Get today's date
endDate = datetime.now()

# Get the data for the desired period <-----------------------------------------
startDate = endDate - timedelta(days=60)  # change to your desired period

# Before reading the CSV file, determine the correct index column name
if interval == '1d':
    index_col_name = 'Date'
else:
    index_col_name = 'Datetime'

# Define the file name for storing the data, ensuring it's saved in the 'data' folder
data_folder = 'sector_analysis/sector_data/input'
if not os.path.exists(data_folder):
    os.makedirs(data_folder)  # Create the data folder if it doesn't exist
# List to store tickers that meet the criteria
identified_tickers = []

for tickerSymbol in tickerSymbols:
    fileName = f"{data_folder}/{tickerSymbol}_data_{startDate.strftime('%Y%m%d')}_{endDate.strftime('%Y%m%d')}_{interval}.csv"

    # Check if data is already downloaded
    if os.path.exists(fileName):
        # Load data from CSV file
        tickerData = pd.read_csv(fileName, parse_dates=True, index_col=index_col_name)
        # Convert index to UTC datetime objects if they are timezone-aware
        if tickerData.index.tz is not None:
            tickerData.index = tickerData.index.tz_convert('UTC')
        else:
            tickerData.index = pd.to_datetime(tickerData.index)
    else:
        # Download data if not already downloaded
        tickerData = yf.download(tickerSymbol, start=startDate, end=endDate, interval=interval)
        tickerData = tickerData.round(2)
        # Ensure the index is in datetime format and convert to UTC if timezone-aware
        tickerData.index = pd.to_datetime(tickerData.index, utc=True)
        # Save data to CSV file
        tickerData.to_csv(fileName)
    # Ensure the index is in datetime format
    tickerData.index = pd.to_datetime(tickerData.index)

    # Convert the dates into string format without time
    tickerData['Date'] = tickerData.index.strftime('%Y-%m-%d %H:%M:%S' if interval != '1d' else '%Y-%m-%d')

    # Calculate body and shadow
    tickerData = calculate_body_and_shadow(tickerData)

    # Identify FVGs
    fvg_list = identify_fvg(tickerData)

    # Identify major highs and lows
    major_highs, major_lows = identify_major_highs_lows(tickerData)

    # Identify break of structure (BoS)
    bos_list = identify_bos(tickerData, major_highs, major_lows)

    # Convert the index to integers for pattern detection
    tickerData.reset_index(drop=True, inplace=True)

    # Set 'Date' as the index
    tickerData.set_index('Date', inplace=True)

    # Ensure the index is a DatetimeIndex and localize or convert timezone if necessary
    if not isinstance(tickerData.index, pd.DatetimeIndex):
        tickerData.index = pd.to_datetime(tickerData.index)

    # Identify demand zones
    demand_zones = identify_demand_zones(tickerData, major_lows, 10, 1.1)

    # Identify supply zones
    supply_zones = identify_supply_zones(tickerData, major_highs, 10, 1.1)  # Adjust parameters as needed

    # Find the closest demand and supply zones
    closest_demand, closest_supply = find_closest_zones(tickerData, demand_zones, supply_zones)

    # Check if both demand and supply zones exist
    if closest_demand is not None and closest_supply is not None:
        # Calculate the split lines
        split1, split2 = calculate_split_lines(tickerData, closest_demand, closest_supply)

        # Get the last close price
        last_close = tickerData.iloc[-1]['Close']

        # Check if the last close price is in the bottom two parts
        if last_close <= split2:
            logging.info(f"{tickerSymbol}: Both demand and supply zones are identified and last close is in the bottom two parts.")
            plot_chart(tickerData, fvg_list, demand_zones, supply_zones, major_highs, major_lows, tickerSymbol)
            identified_tickers.append(tickerSymbol)  # Add ticker to the list
        else:
            logging.info(f"{tickerSymbol}: Last close is not in the bottom two parts.")
    else:
        logging.info(f"{tickerSymbol}: Either demand or supply zones are not identified.")

# Save identified tickers to CSV
output_csv_path = 'sector_analysis/sector_data/output/15m_volatile_with_demand_supply_bottom_2.csv'
identified_tickers_df = pd.DataFrame(identified_tickers, columns=['Ticker'])
identified_tickers_df.to_csv(output_csv_path, index=False)
