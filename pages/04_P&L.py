import streamlit as st

from utils import *

if useWideLayout():
    st.set_page_config(layout="wide")

process_open_trades()
display_pnl()