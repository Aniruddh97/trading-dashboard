import streamlit as st

from utils import *


meta = readJSON(METADATA_FILE_PATH)
selected_ticker = st.selectbox('Search', meta['LIST']['NIFTY 500'])
df = most_recent_data(tickers=[selected_ticker])[selected_ticker]

pattern, rank = getLatestCandlePattern(df=df, all=True)
sri = SupportResistanceIndicator(data=df, tickerName=selected_ticker, patternTitle=pattern)
st.plotly_chart(sri.getIndicator(df.index.stop-1))

with st.form("Order Form"):
	stop_loss = st.number_input("Stoploss")
	target = st.number_input("Target")
	units = st.number_input("Units", 1)
	submitted = st.form_submit_button("Place Order")
	if submitted:
		now_date = df.DATE[df.index.stop-1]
		strike_price = df.CLOSE[df.index.stop-1]
		save_order(
			ticker=selected_ticker, 
			start_date=now_date, 
			strike_price=strike_price,
			target=target,
			stoploss=stop_loss,
			units=units)
		
orders_df = execute_query(ORDER_DATABASE_PATH, query="SELECT * FROM orders")
if orders_df is not None and  not orders_df.empty:
	st.dataframe(orders_df)