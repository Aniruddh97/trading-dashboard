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
    limit_per_page = 10
    if ('watchlist' in st.session_state 
            and len(st.session_state['watchlist']) != 0 
            and (is_market_open() != 1 
            or st.session_state.page != (math.ceil((len(watchlist) / limit_per_page)) - 1))
        ):
        pass
    else:
        st.session_state['watchlist'] = []
        st.session_state['watchlistTickers'] = []
        ohlc_obj_df = most_recent_data(tickers=watchlist[::-1])

        for ticker in ohlc_obj_df:
            df = ohlc_obj_df[ticker]
            pattern, rank = getLatestCandlePattern(df=df, all=True)
            sri = SupportResistanceIndicator(data=df, tickerName=ticker, patternTitle=pattern)
            chart = sri.getIndicator(df.index.stop-1)
            st.session_state['watchlist'].append((ticker,chart))
        
    chartContainer = st.container()
    for ticker, chart in paginate(datalist=st.session_state['watchlist'], limit_per_page=limit_per_page):
        chartContainer.plotly_chart(chart)
        if chartContainer.button(f'Remove `{ticker}` from watchlist'):
            removeFromWatchlist(ticker=ticker)
        
else:
    st.info('Watchlist is empty')
        