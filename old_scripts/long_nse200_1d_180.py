from datetime import datetime, timedelta
from plot_chart import plot_chart
import yfinance as yf
import pandas as pd
from utils import calculate_body_and_shadow, identify_fvg, identify_major_highs_lows, identify_bos, identify_demand_zones, identify_supply_zones, find_closest_zones
import os
import logging
import sys


# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Read ticker symbols from NSE200.csv without a header
tickerSymbols = pd.read_csv('NSE200.csv', header=None)[0].tolist()


# Define the interval (e.g., '1d' for daily, '1h' for hourly, '30m' for 30 minutes)
interval = '1d'  # Change this to your desired interval <----------------------------------------

# Get today's date
endDate = datetime.now()

# Get the data for the desired period <-----------------------------------------
startDate = endDate - timedelta(days=180)  # change to your desired period

# Before reading the CSV file, determine the correct index column name
if interval == '1d':
    index_col_name = 'Date'
else:
    index_col_name = 'Datetime'

# Define the file name for storing the data, ensuring it's saved in the 'data' folder
data_folder = 'data'
if not os.path.exists(data_folder):
    os.makedirs(data_folder)  # Create the data folder if it doesn't exist

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

 # Check if there are any demand zones and if the last close price is less than 5% off the high of the closest demand zone
    demand_condition_met = False
    if closest_demand is not None:
        last_low = tickerData.iloc[-1]['Low']
        closest_demand_high = tickerData.iloc[closest_demand]['High']
        threshold_demand = closest_demand_high * 1.025

        if last_low <= threshold_demand and last_low > closest_demand_high:
            logging.info(f"{tickerSymbol}: Last low is within 5% of the closest demand zone high and higher than the closest demand zone high.")
            demand_condition_met = True
        else:
            logging.info(f"{tickerSymbol}: Last low is not within 5% of the closest demand zone high or not higher than the closest demand zone high.")
    else:
        logging.info(f"{tickerSymbol}: No demand zones identified.")

    # Check if there are any supply zones and if the last high price is at least 5% away from the low of the closest supply zone
    supply_condition_met = False
    if closest_supply is not None:
        last_high = tickerData.iloc[-1]['High']
        closest_supply_low = tickerData.iloc[closest_supply]['Low']
        threshold_supply = closest_supply_low * 0.95

        if last_high < threshold_supply:
            logging.info(f"{tickerSymbol}: Last high is at least 5% away from the closest supply zone low.")
            supply_condition_met = True
        else:
            logging.info(f"{tickerSymbol}: Last high is not at least 5% away from the closest supply zone low.")
    else:
        logging.info(f"{tickerSymbol}: No supply zones identified.")

    # Additional check to ensure both demand and supply zones are present and conditions are met
    if closest_demand is not None and closest_supply is not None and demand_condition_met and supply_condition_met:
        logging.info(f"{tickerSymbol}: Both demand and supply zones are present and conditions are met. Plotting chart.")
        plot_chart(tickerData, fvg_list, demand_zones, supply_zones, major_highs, major_lows, tickerSymbol)
    else:
        logging.info(f"{tickerSymbol}: Conditions not met. Chart will not be plotted.")

    plot_chart(tickerData, fvg_list, demand_zones, supply_zones, major_highs, major_lows, tickerSymbol)
