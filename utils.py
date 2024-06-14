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



def identify_demand_zones(tickerData, major_lows, candles_count, comparison_multiplier):
    """Identify demand zones based on major lows and absolute differences, with customizable parameters for analysis,
    ensuring no candle to the right has a low lower than the high of the demand zone candle."""
    demand_zones = []
    for low_pos in major_lows:
        # Ensure there are enough candles before and after the major low
        if low_pos > candles_count - 1 and low_pos < len(tickerData) - candles_count:
            # Get the 'Low' of the candle 'candles_count' positions before the major low
            pre_low = tickerData.iloc[low_pos - candles_count]['Low']
            # Get the 'Low' of the candle 'candles_count' positions after the major low
            post_low = tickerData.iloc[low_pos + candles_count]['Low']
            # Get the 'High' of the demand zone candle (major low candle)
            demand_zone_high = tickerData.iloc[low_pos]['High']
            major_low = tickerData.iloc[low_pos]['Low']

            # Calculate the absolute differences
            abs_diff_decline = abs(major_low - pre_low)
            abs_diff_increase = abs(post_low - major_low)

            if abs_diff_increase > comparison_multiplier * abs_diff_decline:
                # Check for any candle to the right with a close lower than the close of the demand zone candle
                invalid_zone = False
                for i in range(low_pos + 1, len(tickerData)):
                    if tickerData.iloc[i]['Close'] < tickerData.iloc[low_pos]['Close']:
                        invalid_zone = True
                        # logging.info(f"Candle to the right with lower close found at position {i}, invalidating demand zone at position {low_pos}. Demand zone close: {tickerData.iloc[low_pos]['Close']}, Invalidating candle close: {tickerData.iloc[i]['Close']}")
                        break

                if not invalid_zone:
                    demand_zones.append(low_pos)
                    # logging.info(f"Demand zone identified at position {low_pos} with major low at {major_low}")
    if not demand_zones:
        logging.info("No demand zones were identified.")
    return demand_zones



def identify_supply_zones(tickerData, major_highs, candles_count, comparison_multiplier):
    """Identify supply zones based on major highs and absolute differences, with customizable parameters for analysis,
    ensuring no candle to the right has a high higher than the low of the supply zone candle."""
    supply_zones = []
    for high_pos in major_highs:
        # Ensure there are enough candles before and after the major high
        if high_pos > candles_count - 1 and high_pos < len(tickerData) - candles_count:
            # Get the 'High' of the candle 'candles_count' positions before the major high
            pre_high = tickerData.iloc[high_pos - candles_count]['High']
            # Get the 'High' of the candle 'candles_count' positions after the major high
            post_high = tickerData.iloc[high_pos + candles_count]['High']
            # Get the 'Low' of the supply zone candle (major high candle)
            supply_zone_low = tickerData.iloc[high_pos]['Low']
            major_high = tickerData.iloc[high_pos]['High']

            # Calculate the absolute differences
            abs_diff_increase = abs(major_high - pre_high)
            abs_diff_decline = abs(post_high - major_high)

            # Check if the absolute decline is more than the absolute increase by a factor of the comparison_multiplier
            if abs_diff_decline > comparison_multiplier * abs_diff_increase:
                # Check for any candle to the right with a close higher than the close of the supply zone candle
                invalid_zone = False
                for i in range(high_pos + 1, len(tickerData)):
                    if tickerData.iloc[i]['Close'] > tickerData.iloc[high_pos]['Close']:
                        invalid_zone = True
                        # logging.info(f"Candle to the right with higher close found at position {i}, invalidating supply zone at position {high_pos}. Supply zone close: {tickerData.iloc[high_pos]['Close']}, Invalidating candle close: {tickerData.iloc[i]['Close']}")
                        break

                if not invalid_zone:
                    supply_zones.append(high_pos)
                    # logging.info(f"Supply zone identified at position {high_pos} with major high at {major_high}")


    if not supply_zones:
        logging.info("No supply zones were identified.")
    return supply_zones

