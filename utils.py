import numpy as np
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_body_and_shadow(tickerData):
    """Calculate the body size and the upper and lower shadow sizes."""
    tickerData['Body'] = abs(tickerData['Open'] - tickerData['Close'])
    tickerData['Lower Shadow'] = tickerData[['Open', 'Close']].min(axis=1) - tickerData['Low']
    tickerData['Upper Shadow'] = tickerData['High'] - tickerData[['Open', 'Close']].max(axis=1)
    return tickerData

def identify_fvg(tickerData):
    """Identify Fair Value Gaps (FVG) in the data."""
    fvg_list = []
    for i in range(1, len(tickerData) - 1):
        first_candle = tickerData.iloc[i - 1]
        third_candle = tickerData.iloc[i + 1]
        
        if first_candle['High'] < third_candle['Low']:
            fvg_list.append((i - 1, i + 1, 'Bullish'))
            
        if first_candle['Low'] > third_candle['High']:
            fvg_list.append((i - 1, i + 1, 'Bearish'))
    
    return fvg_list


def identify_major_highs_lows(tickerData, window=5):
    major_highs = []
    major_lows = []

    for i in range(window, len(tickerData) - window):
        current_high = tickerData.iloc[i]['High']
        current_low = tickerData.iloc[i]['Low']
        
        preceding_highs = tickerData.iloc[i - window:i]['High']
        following_highs = tickerData.iloc[i + 1:i + 1 + window]['High']
        preceding_lows = tickerData.iloc[i - window:i]['Low']
        following_lows = tickerData.iloc[i + 1:i + 1 + window]['Low']
        
        if current_high > preceding_highs.max() and current_high > following_highs.max():
            major_highs.append(i)
        
        if current_low < preceding_lows.min() and current_low < following_lows.min():
            major_lows.append(i)
    
    return major_highs, major_lows

def identify_bos(tickerData, major_highs, major_lows):
    bos_list = []

    for i in range(1, len(tickerData)):
        current_candle = tickerData.iloc[i]

        for high_index in major_highs:
            if i > high_index:
                major_high_value = tickerData.iloc[high_index]['High']
                if current_candle['Open'] < major_high_value and current_candle['Close'] > major_high_value:
                    bos_list.append((i, 'Bullish'))
                    break

        for low_index in major_lows:
            if i > low_index:
                major_low_value = tickerData.iloc[low_index]['Low']
                if current_candle['Open'] > major_low_value and current_candle['Close'] < major_low_value:
                    bos_list.append((i, 'Bearish'))
                    break
    
    return bos_list



def identify_demand_zones(tickerData, major_lows):
    """Identify demand zones based on major lows and rate of change."""
    demand_zones = []
    for low_pos in major_lows:
        if low_pos > 0 and low_pos < len(tickerData) - 1:
            pre_low = tickerData.iloc[low_pos - 1]['Low']
            post_low = tickerData.iloc[low_pos + 1]['Low']
            major_low = tickerData.iloc[low_pos]['Low']

            rate_of_decline = (major_low - pre_low) / pre_low
            rate_of_increase = (post_low - major_low) / major_low

            # Check if the rate of decline is less than half of the rate of increase
            if abs(rate_of_decline) < 0.5 * rate_of_increase:
                demand_zones.append(low_pos)
                logging.info(f"Demand zone identified at position {low_pos} with major low at {major_low}")

    if not demand_zones:
        logging.info("No demand zones were identified.")
    return demand_zones