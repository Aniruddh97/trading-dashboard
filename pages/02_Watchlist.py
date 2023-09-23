import streamlit as st

from utils import *
from algo import *

if useWideLayout():
    st.set_page_config(layout="wide")

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
    limit_per_page = 10
    if ('watchlist' in st.session_state 
            and len(st.session_state['watchlist']) != 0 
        ):
        pass
    else:
        st.session_state['watchlist'] = []
        st.session_state['watchlistTickers'] = []
        ohlc_obj_df = most_recent_data(tickers=watchlist[::-1])

        for ticker in ohlc_obj_df:
            df = ohlc_obj_df[ticker]
            pattern, rank = getLatestCandlePattern(df=df, all=True)
            ind = getIndicators(data=df, ticker=ticker, pattern=pattern)[0]
            chart = ind.getIndicator(df.index.stop-1)
            st.session_state['watchlist'].append((ticker,chart))
        
    chartContainer = st.container()
    
    if useSlider():
        chartIndex = st.slider('', min_value=0, max_value=len(st.session_state['watchlist'])-1)
        ticker, chart = st.session_state['watchlist'][chartIndex]
        chartContainer.plotly_chart(chart, use_container_width=True)
        if chartContainer.button(f'Remove `{ticker}` from watchlist'):
            removeFromWatchlist(ticker=ticker)
    else:
        for ticker, chart in paginate(datalist=st.session_state['watchlist'], limit_per_page=limit_per_page):
            chartContainer.plotly_chart(chart, use_container_width=True)
            if chartContainer.button(f'Remove `{ticker}` from watchlist'):
                removeFromWatchlist(ticker=ticker)
        
else:
    st.info('Watchlist is empty')
        
