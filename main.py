import datetime
import pandas as pd
import streamlit as st

from utils import *

with st.sidebar:
    with st.form("Recreate DB Form"):
        duration = st.text_input('Time Duration', '2y')
        submitted = st.form_submit_button("Recreate DB")
        if submitted:
            start_date, end_date = getStartEndDate(duration)
            create_indice_database(start_date=start_date, end_date=end_date)
            create_stock_database(start_date=start_date, end_date=end_date)
            meta = readJSON(METADATA_FILE_PATH)
            meta['last_sync_date'] = end_date
            writeJSON(meta, METADATA_FILE_PATH)

    if st.button("Sync DB"):
        meta = readJSON(METADATA_FILE_PATH)
        if 'last_sync_date' in meta:
            lastSyncDate = datetime.datetime.strptime(meta['last_sync_date'], DATE_FORMAT).date()
            start_date = lastSyncDate + datetime.timedelta(days=1)
            end_date = datetime.date.today()

            if lastSyncDate == end_date:
                st.toast("Data is up-to-date")
            else:
                update_db_data(start_date=start_date, end_date=end_date)
        else:
            st.toast("Please recreate database")


    if st.button("Update Stock List"):
        try:
            nse = NSE()
            meta = readJSON(METADATA_FILE_PATH)

            meta['LIST'] = {}
            meta['LIST']['INDICES'] = nse.fetchIndices()['list']
            whitelist = ["NIFTY 50","NIFTY NEXT 50","NIFTY 100","NIFTY 200","NIFTY 500","NIFTY BANK","NIFTY AUTO","NIFTY FIN SERVICE","NIFTY FINSRV25 50","NIFTY FMCG","NIFTY IT","NIFTY MEDIA"]
            for indice in meta['LIST']['INDICES']:
                try:
                    meta['LIST'][indice] = nse.fetchIndexStocks(indice)['list'][1:]
                except:
                    st.toast(f'Data unavailable for {indice}')

            writeJSON(meta, METADATA_FILE_PATH)
        except Exception:
            st.toast("Update only possible on localhost")
            
    if st.button("Delete all data"):
        dir_name = DATA_DIR_PATH
        directoryItems = os.listdir(dir_name)
        for item in directoryItems:
            os.remove(os.path.join(dir_name, item))


AnalysisTab, StockTab = st.tabs(["Analysis", "Stock"])

with AnalysisTab:
    ohlcData = live_data = None

    with st.form("Indice Selection"):
        meta = readJSON(METADATA_FILE_PATH)
        selected_indice = st.selectbox('Select Index', meta['LIST']['INDICES'])
        submitted = st.form_submit_button("Fetch Live Data")
        if submitted:
            if selected_indice in meta['LIST']:
                tickers = meta['LIST'][selected_indice]
                pbar = st.progress(0, text=f"Fetching live data for '{selected_indice}' stocks")
                
                live_data = get_live_data_collection(tickers=tickers)
                pbar.progress(100, text="Live load completed")

                ohlcData = load_db_data(tickers=tickers)
                ohlcLiveData = merge_data(ohlc_obj_df=ohlcData, data_obj_df=live_data)
                for ticker in ohlcLiveData:
                    st.write(ticker)
                    st.dataframe(ohlcLiveData[ticker])
            else:
                st.toast(f'Company list for \'{selected_indice}\' not available')


with StockTab:
    with st.form("Stock Data"):
        defaultQuery = "SELECT * FROM `TCS`"
        query = st.text_input("SQL Query", defaultQuery)
        option = st.radio("Select Database", ('stock', 'index'))
        submitted = st.form_submit_button("Display")
        if submitted:
            db = INDICE_DATABASE_PATH
            if option == 'stock':
                db = STOCK_DATABASE_PATH
            st.dataframe(execute_query(db, query))
