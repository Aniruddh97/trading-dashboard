import math
import streamlit as st

def paginate(datalist, limit_per_page):
    
    if 'page' not in st.session_state:
        st.session_state.page = 0

    prev, next, _ = st.columns([1, 1, 5])

    last_page = math.ceil((len(datalist) / limit_per_page)) - 1

    if next.button("Next"):
        if st.session_state.page + 1 > last_page:
            st.session_state.page = 0
        else:
            st.session_state.page += 1

    if prev.button("Prev"):
        if st.session_state.page - 1 < 0:
            st.session_state.page = last_page
        else:
            st.session_state.page -= 1

    start_idx = st.session_state.page * limit_per_page
    end_idx = (1 + st.session_state.page) * limit_per_page


    return datalist[start_idx:end_idx]
    