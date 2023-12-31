import os
import shutil
import pandas as pd
import streamlit as st

from algo import *
from utils import *
from zipfile import ZipFile


database, sql, files = st.tabs(["Database", "SQL", "Files"])

with sql:
    form = st.form("Stock Data")
    container = st.container()
    with form:
        defaultQuery = "SELECT * FROM `TCS`"
        query = st.text_input("SQL Query", defaultQuery)
        option = st.radio("Select Database", ('stock', 'index', 'orders'))
        submitted = st.form_submit_button("Display")
        if submitted:
            blacklisted = ['drop', 'alter', 'create', 'truncate', 'insert', 'delete', 'update']
            proceed = True
            for verb in blacklisted:
                if verb in query.lower():
                    st.error('DML operations are not allowed')
                    proceed = False
                    break
                
            if proceed:
                db = STOCK_DATABASE_PATH
                if option == 'index':
                    db = INDICE_DATABASE_PATH
                elif option == 'orders':
                    db = ORDER_DATABASE_PATH
                df = execute_query(db, query)
                container.dataframe(df)
                ind = getIndicators(data=df)[0]
                fig = ind.getIndicator(df.index.stop-1)
                container.plotly_chart(fig, use_container_width=True)

with database:

    st.markdown("""Sync DB""")
    with st.form("Sync DB Form"):
        meta = readJSON(METADATA_FILE_PATH)
        duration = st.text_input('Time Duration', '5d')
        submitted = st.form_submit_button("Sync")
        if submitted:
            start, end = getStartEndDate(timePeriod=duration)
            update_db_data(start_date=start, end_date=end)
            
    st.divider()
    st.markdown("""Recreate""")
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

    st.divider()
    st.markdown("""Reconcile""")
    with st.form("Reconcile Segment Form"):
        meta = readJSON(METADATA_FILE_PATH)
        key = st.selectbox('Segment', meta['LIST'].keys())
        period = st.selectbox('Period', ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'])
        submitted = st.form_submit_button("Reconcile")
        if submitted:
            tickers = meta['LIST'][key]
            db_df_obj = load_db_data(tickers=tickers)
            reconcile_data(df_dict=db_df_obj, period=period)


    st.divider()
    with st.expander("DB Operations"):
        
        if st.button("Backup DB"):
            if os.path.isfile(INDICE_DATABASE_PATH):
                if os.path.isfile(INDICE_DATABASE_BACKUP_PATH):
                    os.remove(INDICE_DATABASE_BACKUP_PATH)
                shutil.copyfile(INDICE_DATABASE_PATH, INDICE_DATABASE_BACKUP_PATH)
            
            if os.path.isfile(STOCK_DATABASE_PATH):
                if os.path.isfile(STOCK_DATABASE_BACKUP_PATH):
                    os.remove(STOCK_DATABASE_BACKUP_PATH)
                shutil.copyfile(STOCK_DATABASE_PATH, STOCK_DATABASE_BACKUP_PATH)

        if st.button("Load Backup DB"):
            if os.path.isfile(INDICE_DATABASE_BACKUP_PATH):
                if os.path.isfile(INDICE_DATABASE_PATH):
                    os.remove(INDICE_DATABASE_PATH)
                shutil.copyfile(INDICE_DATABASE_BACKUP_PATH, INDICE_DATABASE_PATH)
            
            if os.path.isfile(STOCK_DATABASE_BACKUP_PATH):
                if os.path.isfile(STOCK_DATABASE_PATH):
                    os.remove(STOCK_DATABASE_PATH)
                shutil.copyfile(STOCK_DATABASE_BACKUP_PATH, STOCK_DATABASE_PATH)
                

    with st.expander("File Operations"):
        
        if st.button("Clear CSV files"):
            dir_name = DATA_DIR_PATH
            directoryItems = os.listdir(dir_name)
            for item in directoryItems:
                if item.endswith(".csv"):
                    os.remove(os.path.join(dir_name, item))

        if st.button("Delete Orders"):
            if os.path.isfile(ORDER_DATABASE_PATH):
                os.remove(ORDER_DATABASE_PATH)
        
        if st.button("Delete Backup"):
            if os.path.isfile(STOCK_DATABASE_BACKUP_PATH):
                os.remove(STOCK_DATABASE_BACKUP_PATH)
            if os.path.isfile(INDICE_DATABASE_BACKUP_PATH):
                os.remove(INDICE_DATABASE_BACKUP_PATH)

        if st.button("Clear Watchlist"):
            meta = readJSON()
            meta['watchlist'] = []
            writeJSON(meta)
        
        if st.button("Update Metadata"):
            with st.spinner('Updating...'):
                try:
                    nse = NSE()
                    meta = readJSON(METADATA_FILE_PATH)
                    
                    holidays = nse.fetchHolidayList()
                    meta['Holidays'] = holidays

                    meta['LIST'] = {}
                    meta['LIST']['INDICES'] = nse.fetchIndices()['list']
                    for indice in meta['LIST']['INDICES']:
                        try:
                            meta['LIST'][indice] = nse.fetchIndexStocks(indice)['list'][1:]
                        except:
                            st.toast(f'Data unavailable for {indice}')

                    writeJSON(meta, METADATA_FILE_PATH)
                except Exception:
                    st.toast("Update only possible on localhost")


with files:
    dir_name = DATA_DIR_PATH
    directoryItems = os.listdir(dir_name)
    dir_struct = []
    for item in directoryItems:
        size = os.path.getsize(os.path.join(DATA_DIR_PATH, item))/(1024*1024)
        dir_struct.append({
            "File": item,
            "Size (MB)": round(size,2)
        })
    st.dataframe(pd.DataFrame(dir_struct))

    st.divider()
    if st.button("Delete App snapshot"):
        if os.path.isfile('app.zip'):
            os.remove('app.zip')

    st.divider()
    uploaded_file = st.file_uploader("Upload App Snapshot")
    if uploaded_file is not None:
        with ZipFile(uploaded_file, 'r') as zip_ref:
            zip_ref.extractall(DATA_DIR_PATH)
            
    st.divider()
    if st.button("Create App snapshot"):
        if os.path.isfile('app.zip'):
            os.remove('app.zip')

        with ZipFile('app.zip', 'w') as zipObj:
            directoryItems = os.listdir(DATA_DIR_PATH)
            for item in directoryItems:
                if item in ['metadata.json', 'order.sqlite']:
                    file_path = os.path.join(DATA_DIR_PATH, item)
                    zipObj.write(file_path, os.path.basename(file_path))

        with open("app.zip", "rb") as fp:
            st.download_button(
                label="Download App Snapshot",
                data=fp,
                file_name="app.zip",
                mime="application/zip",
                key='download-zip',
            )
