import streamlit as st

from utils import *

if useWideLayout():
	st.set_page_config(layout="wide")

market_status = is_market_open()
if market_status == -1:
	st.error('Market is Closed')
elif market_status == 0:
	st.warning('Error fetching market status')
elif market_status == 1:
	st.success('Market is Open')
