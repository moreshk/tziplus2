import plotly.graph_objects as go
import numpy as np
import logging
import pandas as pd  # Ensure pandas is imported

# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname=s - %(message=s')
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def plot_chart(tickerData, fvg_list, major_highs, major_lows, bos_list):
    """Create a candlestick chart with colored candles, FVGs, and major highs/lows."""
    fig = go.Figure()

    fig.add_trace(go.Candlestick(x=tickerData.index,
                                 open=tickerData['Open'],
                                 high=tickerData['High'],
                                 low=tickerData['Low'],
                                 close=tickerData['Close'],
                                 increasing_line_color='blue',   
                                 decreasing_line_color='black',
                                 name='Price'))

    # Ensure tickerData.index is a DatetimeIndex and convert to string format for comparison
    if not isinstance(tickerData.index, pd.DatetimeIndex):
        tickerData.index = pd.to_datetime(tickerData.index)
    tickerData_dates_str = tickerData.index.strftime('%Y-%m-%d').tolist()

    # Add FVGs to the chart
    for fvg in fvg_list:
        start_date, end_date, fvg_type = fvg
        # Convert start_date and end_date to string for comparison
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        logging.info(f"Checking FVG: start_date={start_date_str}, end_date={end_date_str}")
        if start_date_str in tickerData_dates_str and end_date_str in tickerData_dates_str:
            if fvg_type == 'Bullish':
                color = 'yellow'
                y0 = tickerData.loc[pd.to_datetime(start_date_str)]['High']
                y1 = tickerData.loc[pd.to_datetime(end_date_str)]['Low']
            else:
                color = 'orange'
                y0 = tickerData.loc[pd.to_datetime(start_date_str)]['Low']
                y1 = tickerData.loc[pd.to_datetime(end_date_str)]['High']
            
            logging.info(f"Adding FVG: start_date={start_date_str}, end_date={end_date_str}, y0={y0}, y1={y1}, color={color}")
            
            fig.add_shape(type="rect",
                          x0=start_date_str, x1=end_date_str,
                          y0=y0, y1=y1,
                          fillcolor=color, opacity=0.3, line_width=0)
        else:
            logging.warning(f"Dates not found in tickerData: start_date={start_date_str}, end_date={end_date_str}")

    # Add major highs to the chart
    for high in major_highs:
        high_str = high.strftime('%Y-%m-%d')
        if high_str in tickerData_dates_str:
            y_high = tickerData.loc[pd.to_datetime(high_str)]['High']
            fig.add_shape(type="line",
                          x0=tickerData_dates_str[0], x1=tickerData_dates_str[-1],
                          y0=y_high, y1=y_high,
                          line=dict(color="green", width=1, dash="dash"))  # Thinner line
            # fig.add_annotation(x=high_str, y=y_high, text="Major High", showarrow=True, arrowhead=1)

    # Add major lows to the chart
    for low in major_lows:
        low_str = low.strftime('%Y-%m-%d')
        if low_str in tickerData_dates_str:
            y_low = tickerData.loc[pd.to_datetime(low_str)]['Low']
            fig.add_shape(type="line",
                          x0=tickerData_dates_str[0], x1=tickerData_dates_str[-1],
                          y0=y_low, y1=y_low,
                          line=dict(color="red", width=1, dash="dash"))  # Thinner line
            # fig.add_annotation(x=low_str, y=y_low, text="Major Low", showarrow=True, arrowhead=1)

# Add BoS to the chart
    for bos in bos_list:
        bos_date, bos_type = bos
        bos_date_str = bos_date.strftime('%Y-%m-%d')
        if bos_date_str in tickerData_dates_str:
            y_bos = tickerData.loc[pd.to_datetime(bos_date_str)]['Close']
            color = 'blue' if bos_type == 'Bullish' else 'red'
            fig.add_shape(type="line",
                          x0=bos_date_str, x1=bos_date_str,
                          y0=tickerData['Low'].min(), y1=tickerData['High'].max(),
                          line=dict(color=color, width=2, dash="dot"))
            # fig.add_annotation(x=bos_date_str, y=y_bos, text=f"{bos_type} BoS", showarrow=True, arrowhead=1)


    # New feature: Check for significant drop post major high with adjusted condition
    for high_date in major_highs:
        high_date_str = high_date.strftime('%Y-%m-%d')
        if high_date_str in tickerData_dates_str:
            high_index = tickerData_dates_str.index(high_date_str)
            # Ensure there are enough candles before and after the major high
            if high_index > 4 and high_index + 5 < len(tickerData):
                pre_high_data = tickerData.iloc[high_index-5:high_index]
                post_high_data = tickerData.iloc[high_index+1:high_index+6]
                
                pre_high_increase_rate = (tickerData.iloc[high_index]['High'] - pre_high_data['Low'].min()) / 5
                post_high_decline_rate = (post_high_data['High'].max() - tickerData.iloc[high_index+5]['Low']) / 5
                
                # Check if the rate of decline is at least twice the rate of increase
                if post_high_decline_rate >= 2 * pre_high_increase_rate:
                    logging.info(f"Significant drop identified post major high on {high_date_str}, with the drop rate at least twice the increase rate")
                    fig.add_shape(type="rect",
                                x0=high_date_str, x1=tickerData_dates_str[-1],
                                y0=tickerData.iloc[high_index]['Low'], y1=tickerData.iloc[high_index]['High'],
                                line=dict(color="red", width=3, dash="dash"),
                                fillcolor="red", opacity=0.2)

    # New feature: Check for significant increase post major low with adjusted condition
    for low_date in major_lows:
        low_date_str = low_date.strftime('%Y-%m-%d')
        if low_date_str in tickerData_dates_str:
            low_index = tickerData_dates_str.index(low_date_str)
            # Ensure there are enough candles before and after the major low
            if low_index > 4 and low_index + 5 < len(tickerData):
                pre_low_data = tickerData.iloc[low_index-5:low_index]
                post_low_data = tickerData.iloc[low_index+1:low_index+6]
                
                pre_low_decrease_rate = (pre_low_data['Low'].min() - tickerData.iloc[low_index]['Low']) / 5
                post_low_increase_rate = (tickerData.iloc[low_index+5]['High'] - post_low_data['Low'].min()) / 5
                
                # Check if the rate of increase is at least twice the rate of decrease
                if post_low_increase_rate >= 2 * pre_low_decrease_rate:
                    logging.info(f"Significant increase identified post major low on {low_date_str}, with the increase rate at least twice the decrease rate")
                    fig.add_shape(type="rect",
                                x0=low_date_str, x1=tickerData_dates_str[-1],
                                y0=tickerData.iloc[low_index]['Low'], y1=tickerData.iloc[low_index]['High'],
                                line=dict(color="blue", width=3, dash="dash"),
                                fillcolor="blue", opacity=0.3)
                    
    fig.update_layout(
        yaxis_title='Price',
        xaxis_title='Date',
        xaxis=dict(
            rangeslider=dict(visible=True),
            type='category'  # this line will remove the gaps for non-trading days
        ),
    )

    # Show the figure
    fig.show()