import streamlit as st

from utils import *

meta = readJSON()

with st.form('Configure settings'):
    pivot_window = st.number_input("Pivot Window", min_value=11, max_value=61)
    submitted = st.form_submit_button("Save")
    if submitted:
        if 'settings' not in meta:
            meta['settings'] = {}

        meta['settings']['pivot_window'] = int(pivot_window)
        writeJSON(obj=meta)