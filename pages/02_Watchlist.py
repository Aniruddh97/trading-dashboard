import streamlit as st

from utils import *
from algo import *


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
        addToWatchlist(ticker=ticker)

with st.form('Remove to watchlist'):
    ticker = st.selectbox('Search', meta['watchlist'])
    submitted = st.form_submit_button("Remove from watchlist")
    if submitted:
        removeFromWatchlist(ticker=ticker)

watchlist = meta['watchlist']
if len(watchlist) > 0:
    if 'watchlist' in st.session_state and len(st.session_state['watchlist']) != 0 and is_market_open() != 1:
        pass
    else:
        st.session_state['watchlist'] = []
        
        live_data = {}
        page = 0
        if 'page' in st.session_state:
            page = st.session_state.page
        if is_market_open() == 1 and page == 0:
            live_data = get_live_data_collection(tickers=watchlist)


        ohlc_obj_df = load_db_data(watchlist)
        ohlc_obj_df = append_data(ohlc_obj_df=ohlc_obj_df, data_obj_df=live_data)
        
        for ticker in ohlc_obj_df:
            df = ohlc_obj_df[ticker]
            pattern, rank = getLatestCandlePattern(df=df, all=True)
            sri = SupportResistanceIndicator(data=df, window=11, backCandles=5, tickerName=ticker, patternTitle=pattern)
            chart = sri.getIndicator(df.index.stop-1)
            st.session_state['watchlist'].append(chart)
        
    chartContainer = st.container()
    for chart in paginate(datalist=st.session_state['watchlist'], limit_per_page=10):
        chartContainer.plotly_chart(chart)
        
else:
    st.info('Watchlist is empty')
        
