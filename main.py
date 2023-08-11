import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import sqlite3

from utils import *

with st.sidebar:
    with st.form("Recreate DB Form"):
        duration = st.text_input('Time Duration', '2y')
        submitted = st.form_submit_button("Recreate DB")
        if submitted:
            create_indice_database(duration=duration)
            create_stock_database(duration=duration)
            meta = readJSON('./data/metadata.json')
            meta['last_update_date'] = datetime.date.today()
            writeJSON(meta, './data/metadata.json')

    if st.button("Sync DB"):
        meta = readJSON('./data/metadata.json')
        lastUpdateDate = datetime.datetime.strptime(meta['last_update_date'], '%Y-%m-%d').date()
        start_date = lastUpdateDate + datetime.timedelta(days=1)
        end_date = datetime.date.today()

        if lastUpdateDate == end_date:
            st.toast("Data is up-to-date")
        else:
            update_db_data(start_date=start_date, end_date=end_date)


pbar = st.progress(0, text="Initializing NSE session")
nse = NSE()
pbar.progress(100, text="Fetching indices list")
liveIndexData = nse.fetchIndices()
pbar.progress(100, text="Fetch complete")
ohlcData = liveStockData = None

with st.form("Indice Selection"):
    selected_ticker = st.selectbox('Select Index', liveIndexData['list'])
    submitted = st.form_submit_button("Fetch Live Data")
    if submitted:
        pbar.progress(0, text=f"Fetching '{selected_ticker}' stocks")
        liveStockData = nse.fetchIndexStocks(selected_ticker)
        pbar.progress(100, text="NSE data load completed")

        ohlcData = load_db_data(liveStockData['list'])
        ohlcData = merge_with_live(ohlcData, liveStockData['data'])
        st.write(ohlcData)


defaultQuery = "SELECT * FROM `TCS`"
query = st.text_input("SQL Query", defaultQuery)
st.dataframe(execute_query('./data/stock_database.sqlite', query))

# data = yf.download('INFY.NS', interval='1d', period = '1y', progress=False)
# data.insert(loc=0, column='Date', value=data.index)
# data['Date'] = pd.to_datetime(data.Date).dt.date
# data.set_index('Date').reset_index()
# data = data.drop(['Date'], axis=1)

# if 'Adj Close' in data:
#     data = data.drop(['Close'], axis=1)
#     data.rename(columns={'Adj Close': 'Close'}, inplace=True)

# data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
# st.dataframe(data)

