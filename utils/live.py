import pandas as pd
import yfinance as yf
import streamlit as st

def get_live_data(ticker, period='1d', interval='1d'):
    if 'NS' not in ticker:
        ticker = ticker + '.NS'

    data = yf.download(ticker, interval=interval, period=period, progress=False)
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
    data.CLOSE = data.CLOSE.round(2)
    
    data = data[['DATE', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']]

    # if period == '1d' and interval == '1d' and not data.empty:
    #     first = data.head(1)
    #     last = get_live_data(ticker=ticker, period=period, interval='1m').tail(1)
    #     return pd.DataFrame([{
    #         'DATE': first.DATE[first.index.stop-1],
    #         'OPEN': first.OPEN[first.index.stop-1],
    #         'HIGH': first.HIGH[first.index.stop-1],
    #         'LOW': first.LOW[first.index.stop-1],
    #         'CLOSE': last.CLOSE[last.index.stop-1],
    #         'VOLUME': first.VOLUME[first.index.stop-1],
    #     }])
    return data


def get_live_data_collection(tickers, period='1d', progress=True):
    i=0
    live_collection = {}
    
    pbar = None
    if progress:
        pbar = st.progress(0, text=f"Fetching live data")

    for ticker in tickers:
        i += 1
        try:
            if progress:
                pbar.progress(int((i)*(100/len(tickers))), text=f"Loading live data : {ticker}")
            
            live_collection[ticker] = get_live_data(ticker=ticker, period=period)
        except:
             st.toast(f'Live data unavailable for {ticker}')
             continue
    
    if progress:
        pbar.progress(100, text="Live data load completed")
        
    return live_collection