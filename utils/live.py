import pandas as pd
import yfinance as yf
import streamlit as st

def get_live_data(ticker, period='1d'):
    if 'NS' not in ticker:
        ticker = ticker + '.NS'

    data = yf.download(ticker, interval='1d', period=period, progress=False)
    if len(data.columns) != 6:
        raise Exception(f"{ticker} data not found")

    data.insert(loc=0, column='Date', value=data.index)
    data.insert(loc=0, column='index', value=list(range(0,len(data.index))))
    data['Date'] = pd.to_datetime(data.Date).dt.date
    data = data.set_index('index').reset_index().drop(['index'], axis=1)
    if 'Adj Close' in data:
        data = data.drop(['Close'], axis=1)
        data.rename(columns={'Adj Close': 'Close'}, inplace=True)
    data.rename(columns={'Date': 'DATE', 'Open': 'OPEN', 'High': 'HIGH','Low': 'LOW', 'Close': 'CLOSE', 'Volume': 'VOLUME'}, inplace=True)
    
    data.OPEN = data.OPEN.round(2)
    data.HIGH = data.HIGH.round(2)
    data.LOW = data.LOW.round(2)
    data.CLOSE = data.OPEN.round(2)
    
    return data[['DATE', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']]


def get_live_data_collection(tickers, period='1d'):
    i=0
    live_collection = {}
    pbar = st.progress(0, text=f"Fetching live data")
    for ticker in tickers:
        i += 1
        try:
            pbar.progress(int((i)*(100/len(tickers))), text=f"Loading live data : {ticker}")
            live_collection[ticker] = get_live_data(ticker=ticker, period=period)
        except:
             st.toast(f'Live data unavailable for {ticker}')
             continue
    pbar.progress(100, text="Live data load completed")
    return live_collection