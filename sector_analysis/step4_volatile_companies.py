import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the input and output folders
input_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sector_data', 'output')
output_folder = input_folder

# Read the step3_performance_comparison.csv
candidates_df = pd.read_csv(os.path.join(input_folder, 'step3_performance_comparison.csv'))

# Define the period for fetching data (7 days)
endDate = datetime.now()
startDate = endDate - timedelta(days=7)

# Initialize a list to store tickers with sufficient volatility
volatile_tickers = []

# Function to check if the data is trending in one direction
# Function to check if the data is trending in one direction
def is_trending(data):
    higher_highs = all(data['High'].iloc[i] > data['High'].iloc[i-1] for i in range(1, len(data)))
    higher_lows = all(data['Low'].iloc[i] > data['Low'].iloc[i-1] for i in range(1, len(data)))
    lower_highs = all(data['High'].iloc[i] < data['High'].iloc[i-1] for i in range(1, len(data)))
    lower_lows = all(data['Low'].iloc[i] < data['Low'].iloc[i-1] for i in range(1, len(data)))
    return (higher_highs and higher_lows) or (lower_highs and lower_lows)


# Fetch data and calculate volatility
for _, row in candidates_df.iterrows():
    ticker = row['Ticker']
    sector = row['Sector']
    performance = row['Change in Daily Average %']

    if performance <= 0:
        continue

    data = yf.download(ticker, start=startDate, end=endDate)
    if data.empty:
        continue

    # Calculate daily volatility
    data['Volatility'] = (data['High'] - data['Low']) / data['Low'] * 100

    # Check if the data is trending
    trending = is_trending(data)
    logging.info(f"{ticker}: Trending status - {trending}")

    # Set the volatility threshold
    threshold = 1 if trending else 2

    # Calculate average volatility
    avg_volatility = data['Volatility'].mean()

    # Check if the average volatility meets the criteria
    if avg_volatility >= threshold:
        volatile_tickers.append([ticker, sector, performance, avg_volatility])

# Convert to DataFrame
# volatile_df = pd.DataFrame(volatile_tickers, columns=['Ticker', 'Sector', 'Performance', 'Average Volatility'])
volatile_df = pd.DataFrame(volatile_tickers, columns=['Ticker', 'Sector', 'Change in Daily Average %', 'Average Volatility'])

# Format the numeric columns to 3 decimal places
volatile_df['Change in Daily Average %'] = volatile_df['Change in Daily Average %'].round(3)
volatile_df['Average Volatility'] = volatile_df['Average Volatility'].round(3)

# Sort the DataFrame by Average Volatility in descending order
volatile_df = volatile_df.sort_values('Average Volatility', ascending=False)

# Save the filtered data to a new CSV file
volatile_df.to_csv(os.path.join(output_folder, 'step4_volatile_tickers.csv'), index=False)

print("Filtered volatile tickers saved to step4_volatile_tickers.csv")