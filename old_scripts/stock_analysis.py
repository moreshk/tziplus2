import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os

def load_company_data(file_path):
    df = pd.read_csv(file_path)
    return df[['Company Name', 'Industry', 'Symbol']]

def fetch_stock_data(symbol, start_date, end_date):
    # Add the ".ns" suffix to the symbol
    modified_symbol = f"{symbol}.NS"
    ticker = yf.Ticker(modified_symbol)
    data = ticker.history(start=start_date, end=end_date)
    return data['Close']

def calculate_returns(data):
    if len(data) < 2:
        return None
    return (data.iloc[-1] / data.iloc[0] - 1) * 100

def process_stocks(companies, start_date, end_date):
    results = []
    for _, row in companies.iterrows():
        try:
            data = fetch_stock_data(row['Symbol'], start_date, end_date)
            returns = calculate_returns(data)
            if returns is not None:
                results.append({
                    'Company': row['Company Name'],
                    'Industry': row['Industry'],
                    'Symbol': row['Symbol'],
                    'Returns': returns
                })
            else:
                print(f"Insufficient data for {row['Symbol']}")
        except Exception as e:
            print(f"Error processing {row['Symbol']}: {e}")
    return pd.DataFrame(results)

def main():
    companies = load_company_data('ind_nifty200list.csv')
    
    end_date = datetime.now()
    date_ranges = {
        '1 month': end_date - timedelta(days=30),
        '3 months': end_date - timedelta(days=90),
        '6 months': end_date - timedelta(days=180)
    }
    
    results = {}
    for period, start_date in date_ranges.items():
        results[period] = process_stocks(companies, start_date, end_date)
    
    return results

if __name__ == "__main__":
    results = main()
    print(results)