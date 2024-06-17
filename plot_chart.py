import plotly.graph_objects as go
import logging
import pandas as pd
import numpy as np  # Ensure NumPy is imported
from utils import is_boring_candle, is_exciting_candle, calculate_average_body_size, calculate_average_volume, identify_trend, find_closest_zones, calculate_split_lines

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_nearest_date(index, target):
    """Find the nearest date in the index to the target."""
    # If the index is timezone-aware and the target is not, localize the target to the index's timezone
    if index.tz is not None and target.tzinfo is None:
        target = target.tz_localize(index.tz)
    # If the index is timezone-naive and the target is timezone-aware, remove the timezone from the target
    elif index.tz is None and target.tzinfo is not None:
        target = target.tz_localize(None)
    
    # Calculate the absolute difference between the target and each datetime in the index, then find the index of the minimum difference
    nearest_index = np.abs(index - target).argmin()
    return index[nearest_index]
from utils import is_boring_candle, is_exciting_candle, calculate_average_body_size, calculate_average_volume, identify_trend
from utils import is_boring_candle, is_exciting_candle, calculate_average_body_size, calculate_average_volume, identify_trend

def plot_chart(tickerData, fvg_list, demand_zones, supply_zones, major_highs, major_lows, tickerSymbol):
    """Create a candlestick chart with colored candles, FVGs, major highs/lows, volume, and trend arrows."""
    fig = go.Figure()

    # Calculate average body size and volume for boring and exciting candle detection
    average_body_size = calculate_average_body_size(tickerData)
    average_volume = calculate_average_volume(tickerData)

    # Add volume data as a bar chart on a secondary y-axis
    max_volume = tickerData['Volume'].max()
    scaled_volume = tickerData['Volume'] / max_volume * 0.5 * tickerData['High'].max()
    fig.add_trace(go.Bar(x=tickerData.index,
                         y=scaled_volume,
                         name='Volume',
                         marker_color='lightgrey',
                         opacity=0.6, 
                         yaxis='y2'))
    
    # Add candlestick data with custom colors
    for i in range(len(tickerData)):
        candle = tickerData.iloc[i]
        is_boring = is_boring_candle(candle, average_body_size, average_volume)
        is_exciting, candle_type = is_exciting_candle(candle, average_body_size, average_volume)

        pattern_shape = None  # Initialize pattern_shape

        if is_boring:
            color = 'white'
            line_color = 'blue' if candle['Close'] > candle['Open'] else 'black'
        elif is_exciting:
            if candle_type == 'Bullish':
                color = 'green'
                line_color = 'green'
                # pattern_shape = 'x'
            else:
                color = 'black'
                line_color = 'black'
        else:
            color = 'blue' if candle['Close'] > candle['Open'] else 'black'
            line_color = color

        fig.add_trace(go.Candlestick(
            x=[candle.name],
            open=[candle['Open']],
            high=[candle['High']],
            low=[candle['Low']],
            close=[candle['Close']],
            increasing_line_color=line_color,
            decreasing_line_color=line_color,
            increasing_fillcolor=color,
            decreasing_fillcolor=color,
            name='Price',
            showlegend=False,
            hoverinfo='x+y+name'
        ))

        if pattern_shape:
            fig.add_trace(go.Scatter(
                x=[candle.name],
                y=[candle['Close']],
                mode='markers',
                marker=dict(
                    symbol=pattern_shape,
                    size=10,
                    color='green' if candle_type == 'Bullish' else 'red'
                ),
                showlegend=False,
                hoverinfo='skip'
            ))

    # Identify trends based on major highs and lows
    trends = identify_trend(tickerData, major_highs, major_lows)
    for i, trend in enumerate(trends):
        arrow_symbol = 'triangle-up' if trend == 'up' else 'triangle-down' if trend == 'down' else 'triangle-right'
        fig.add_trace(go.Scatter(
            x=[tickerData.index[i]],
            y=[tickerData['Low'].min() * 0.95],  # Position the arrow slightly below the lowest low
            mode='markers',
            marker=dict(
                symbol=arrow_symbol,
                size=10,
                color='blue'
            ),
            name='Trend',
            showlegend=False,
            hoverinfo='skip'
        ))

    # Modify FVGs to the chart based on position
    for fvg in fvg_list:
        start_pos, end_pos, fvg_type = fvg  # Use positions instead of dates
        color = 'yellow' if fvg_type == 'Bullish' else 'orange'
        y0 = tickerData.iloc[start_pos]['High'] if fvg_type == 'Bullish' else tickerData.iloc[start_pos]['Low']
        y1 = tickerData.iloc[end_pos]['Low'] if fvg_type == 'Bullish' else tickerData.iloc[end_pos]['High']
        
        fig.add_shape(type="rect",
                      x0=tickerData.index[start_pos], x1=tickerData.index[end_pos],
                      y0=y0, y1=y1,
                      fillcolor=color, opacity=0.3, line_width=2)

    # Add demand zones to the chart
    for zone_pos in demand_zones:
        if tickerData.iloc[-1]['Close'] > tickerData.iloc[zone_pos]['Low']:  # Check if the latest close price is above the major low
            x0 = tickerData.index[zone_pos]  # Left side of the rectangle
            x1 = tickerData.index[-1]  # Right side of the rectangle extends to the end
            y0 = tickerData.iloc[zone_pos]['Low']  # Bottom of the rectangle
            y1 = tickerData.iloc[zone_pos]['High']  # Top of the rectangle, changed from y0 to represent the high of the candle

            fig.add_shape(type="rect",
                        x0=x0, x1=x1,
                        y0=y0, y1=y1,
                             fillcolor="blue", opacity=0.3, line_width=0)

    # Add supply zones to the chart
    for zone_pos in supply_zones:
        if tickerData.iloc[-1]['Close'] < tickerData.iloc[zone_pos]['High']:  # Check if the latest close price is below the major high
            x0 = tickerData.index[zone_pos]  # Left side of the rectangle
            x1 = tickerData.index[-1]  # Right side of the rectangle extends to the end
            y0 = tickerData.iloc[zone_pos]['Low']  # Bottom of the rectangle
            y1 = tickerData.iloc[zone_pos]['High']  # Top of the rectangle

            fig.add_shape(type="rect",
                        x0=x0, x1=x1,
                        y0=y0, y1=y1,
                        fillcolor="black", opacity=0.3, line_width=0)
            
    # Add horizontal dashed lines for major highs and lows
    for high in major_highs:
        fig.add_shape(type="line",
                      x0=tickerData.index[high], x1=tickerData.index[-1],
                      y0=tickerData.iloc[high]['High'], y1=tickerData.iloc[high]['High'],
                      line=dict(color="blue", width=2, dash="dash"),
                      opacity=0.1)

    for low in major_lows:
        fig.add_shape(type="line",
                      x0=tickerData.index[low], x1=tickerData.index[-1],
                      y0=tickerData.iloc[low]['Low'], y1=tickerData.iloc[low]['Low'],
                      line=dict(color="black", width=2, dash="dash"),
                      opacity=0.1)

    # Find the closest demand and supply zones
    closest_demand, closest_supply = find_closest_zones(tickerData, demand_zones, supply_zones)

    # Calculate the points for the two lines
    split1, split2 = calculate_split_lines(tickerData, closest_demand, closest_supply)

    # Add the two lines to the chart
    fig.add_shape(type="line",
                  x0=tickerData.index[closest_demand], x1=tickerData.index[-1],
                  y0=split1, y1=split1,
                  line=dict(color="black", width=2, dash="dot"))

    fig.add_shape(type="line",
                  x0=tickerData.index[closest_demand], x1=tickerData.index[-1],
                  y0=split2, y1=split2,
                  line=dict(color="black", width=2, dash="dot"))

    # Determine the interval of the data
    data_interval = tickerData.index[1] - tickerData.index[0]

    # Set x-axis tick format based on the interval
    if data_interval.days >= 1:
        # Daily data or greater, show date in dd-mm format
        tickformat = '%d-%m'
    else:
        # Hourly or minute data, show time in hh:mm format
        tickformat = '%H:%M'

    fig.update_layout(
        title=f"Ticker: {tickerSymbol}",
        yaxis_title='Price',
        xaxis_title='Date',
        xaxis=dict(
            rangeslider=dict(visible=True),
            type='category',  # this line will remove the gaps for non-trading days
            tickformat=tickformat,  # Set the tick format based on the data interval
        ),
        yaxis=dict(
            title='Price',
            domain=[0.3, 1]  # Adjust the domain to leave space for the volume bars
        ),
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right',
            showgrid=False,
            domain=[0, 0.2],  # Adjust the domain to position the volume bars below the price chart
        ),
        height=1000  # Adjust this value as needed to make the chart taller
    )

    # Show the figure
    fig.show()