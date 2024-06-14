import plotly.graph_objects as go
import logging
import pandas as pd
import numpy as np  # Ensure NumPy is imported

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


def plot_chart(tickerData, fvg_list, major_highs, major_lows, bos_list, demand_zones, supply_zones, tickerSymbol):
    """Create a candlestick chart with colored candles, FVGs, major highs/lows, and volume."""
    fig = go.Figure()

    

    # Scale volume data to 50% of the chart height
    max_volume = tickerData['Volume'].max()
    scaled_volume = tickerData['Volume'] / max_volume * 0.5 * tickerData['High'].max()

    # Add volume data as a bar chart on a secondary y-axis
    fig.add_trace(go.Bar(x=tickerData.index,
                         y=scaled_volume,
                         name='Volume',
                         marker_color='lightgrey',
                         opacity=0.6, 
                         yaxis='y2'))
    
    fig.add_trace(go.Candlestick(x=tickerData.index,
                                 open=tickerData['Open'],
                                 high=tickerData['High'],
                                 low=tickerData['Low'],
                                 close=tickerData['Close'],
                                 increasing_line_color='blue',   
                                 decreasing_line_color='black',
                                 name='Price'))

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

    # Modify major highs to the chart to extend only to the right
    for high_pos in major_highs:
        y_high = tickerData.iloc[high_pos]['High']
        x_high_date = tickerData.index[high_pos]  # Get the date/index of the high
        
        fig.add_shape(type="line",
                      x0=x_high_date, x1=tickerData.index[-1],  # Start from the high and extend to the end
                      y0=y_high, y1=y_high,
                      line=dict(color="green", width=1, dash="dash"))

    # Modify major lows to the chart to extend only to the right
    for low_pos in major_lows:
        y_low = tickerData.iloc[low_pos]['Low']
        x_low_date = tickerData.index[low_pos]  # Get the date/index of the low
        
        fig.add_shape(type="line",
                      x0=x_low_date, x1=tickerData.index[-1],  # Start from the low and extend to the end
                      y0=y_low, y1=y_low,
                      line=dict(color="black", width=1, dash="dot"))

    # Modify BoS to the chart based on position
    for bos in bos_list:
        bos_pos, bos_type = bos
        y_bos = tickerData.iloc[bos_pos]['Close']
        color = 'blue' if bos_type == 'Bullish' else 'red'
        
        fig.add_shape(type="line",
                      x0=tickerData.index[bos_pos], x1=tickerData.index[bos_pos],
                      y0=tickerData['Low'].min(), y1=tickerData['High'].max(),
                      line=dict(color=color, width=2, dash="dot"))

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