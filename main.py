import shutil
import datetime
import pandas as pd
import streamlit as st
import extra_streamlit_components as stx

from algo import *
from utils import *


with st.sidebar:
    
    if 'status' not in st.session_state:
        market_status = is_market_open()
        st.session_state['status'] = market_status
    else:
        market_status= st.session_state['status']
    
    if market_status == -1:
        st.error('Market is Closed')
    elif market_status == 0:
        st.warning('Error fetching market status')
    elif market_status == 1:
        st.success('Market is Open')
    
        
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


    with st.expander("DB Operations"):

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
                



    with st.expander("Other Operations"):

        if st.button("Clear CSV files"):
            # remove csv files
            dir_name = DATA_DIR_PATH
            directoryItems = os.listdir(dir_name)
            for item in directoryItems:
                if item.endswith(".csv"):
                    os.remove(os.path.join(dir_name, item))

        if st.button("Update Stock List"):
            try:
                nse = NSE()
                meta = readJSON(METADATA_FILE_PATH)

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
        

        if st.button("Refresh Market Status"):
            st.session_state['status'] = is_market_open()

        
chosen_tab = stx.tab_bar(data=[
    stx.TabBarItemData(id="analysis", title="Analysis", description=""),
    stx.TabBarItemData(id="watchlist", title="Watchlist", description=""),
    stx.TabBarItemData(id="stock", title="Stock", description=""),
    stx.TabBarItemData(id="files", title="Files", description="")])

if chosen_tab == "analysis":
    ohlcData = live_data = None

    with st.form("Indice Selection"):
        try:
            meta = readJSON(METADATA_FILE_PATH)
            selected_indice = st.selectbox('Select Index', meta['LIST']['INDICES'])
            submitted = st.form_submit_button("Fetch Live Data")
            if submitted:
                st.session_state['analysis'] = {}
                if selected_indice in meta['LIST']:
                    tickers = meta['LIST'][selected_indice]
                    
                    live_data = {}
                    if st.session_state['status'] == 1:
                        live_data = get_live_data_collection(tickers=tickers)

                    ohlcData = load_db_data(tickers=tickers)
                    ohlcLiveData = merge_data(ohlc_obj_df=ohlcData, data_obj_df=live_data)
                    
                    i = 0
                    analysis = {}
                    analysis['data'] = {}
                    analysis['rank'] = []
                    pbar = st.progress(0, text=f"Analyzing data")
                    for ticker in ohlcLiveData:
                        i += 1
                        pbar.progress(int((i)*(100/len(tickers))), text=f"Analyzing {ticker}")

                        df = ohlcLiveData[ticker]
                        df = recognizePattern(df, all=False)
                        sri = SupportResistanceIndicator(df, 11, 5, ticker)

                        candleIndex = df.index.stop-1
                        analysis['data'][ticker] = sri.getIndicator(candleIndex)
                        analysis['rank'].append({
                            'Ticker': ticker,
                            'Pattern': df['candlestick_pattern'][candleIndex],
                            'Pattern Rank': df['candlestick_rank'][candleIndex],
                        })

                    pbar.progress(100, text=f"Analysis complete")
                    st.session_state['analysis'] = analysis
                else:
                    st.toast(f'Company list for \'{selected_indice}\' not available')
        except Exception as e:
            st.toast(str(e))

    if 'analysis' in st.session_state and 'rank' in st.session_state['analysis']:
        rank = pd.DataFrame(st.session_state['analysis']['rank'])
        rank = rank.sort_values(by='Pattern Rank', ascending=True)
        rank_for_display = rank[rank.Pattern != 'NO_PATTERN']
        if not rank_for_display.empty:
            st.dataframe(rank_for_display)

        indicator_obj = st.session_state['analysis']['data']
        for ticker in rank.Ticker.to_list():
            st.plotly_chart(indicator_obj[ticker])


if chosen_tab == "watchlist":
    meta = readJSON()
    tickerList = []
    if 'LIST' in meta:
        tickerList = list(set([ticker for indice in meta['LIST'] for ticker in meta['LIST'][indice]]))
    if 'watchlist' not in meta:
        meta['watchlist'] = []
        st.session_state['watchlist'] = []

    with st.form('Add to watchlist'):
        ticker = st.selectbox('Search', tickerList)
        submitted = st.form_submit_button("Add to watchlist")
        if submitted:
            meta['watchlist'].append(ticker)
            writeJSON(meta)
            st.session_state['watchlist'] = []

    with st.form('Remove to watchlist'):
        ticker = st.selectbox('Search', meta['watchlist'])
        submitted = st.form_submit_button("Remove from watchlist")
        if submitted:
            meta['watchlist'].remove(ticker)
            writeJSON(meta)

    watchlist = meta['watchlist']
    if len(watchlist) > 0:
        if 'watchlist' in st.session_state and len(st.session_state['watchlist']) != 0 and st.session_state['status'] != 1:
            for chart in st.session_state['watchlist']:
                st.plotly_chart(chart)
        else:
            st.session_state['watchlist'] = []
            
            live_data = {}
            if st.session_state['status'] == 1:
                live_data = get_live_data_collection(tickers=watchlist)
            ohlc_obj_df = load_db_data(watchlist)
            ohlc_obj_df = merge_data(ohlc_obj_df=ohlc_obj_df, data_obj_df=live_data)
            
            for ticker in ohlc_obj_df:
                df = ohlc_obj_df[ticker]
                df = recognizePattern(df, all=True)
                sri = SupportResistanceIndicator(df, 11, 5, ticker)
                chart = sri.getIndicator(df.index.stop-1)
                st.plotly_chart(chart)
                st.session_state['watchlist'].append(chart)
            
    else:
        st.info('Watchlist is empty')
        

if chosen_tab == "stock":
    form = st.form("Stock Data")
    container = st.container()

    with form:
        defaultQuery = "SELECT * FROM `TCS`"
        query = st.text_input("SQL Query", defaultQuery)
        option = st.radio("Select Database", ('stock', 'index'))
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
                db = INDICE_DATABASE_PATH
                if option == 'stock':
                    db = STOCK_DATABASE_PATH
                df = execute_query(db, query)
                container.dataframe(df)
                fig = SupportResistanceIndicator(df, 11, 5, "").getIndicator(df.index.stop-1)
                container.plotly_chart(fig)

if chosen_tab == "files":
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