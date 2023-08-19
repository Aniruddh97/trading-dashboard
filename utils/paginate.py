import math
import streamlit as st

def paginate(datalist, limit_per_page):
    
    if 'page' not in st.session_state:
        st.session_state.page = 0

    cols = st.columns(5)
    last_page = math.ceil((len(datalist) / limit_per_page)) - 1

    if cols[2].button(":point_right:"):
        if st.session_state.page + 1 > last_page:
            st.session_state.page = 0
        else:
            st.session_state.page += 1

    if cols[0].button(":point_left:"):
        if st.session_state.page - 1 < 0:
            st.session_state.page = last_page
        else:
            st.session_state.page -= 1

    cols[1].write(st.session_state.page)

    start_idx = st.session_state.page * limit_per_page
    end_idx = (1 + st.session_state.page) * limit_per_page


    return datalist[start_idx:end_idx]
    