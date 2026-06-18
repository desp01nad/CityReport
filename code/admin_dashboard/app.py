import streamlit as st

st.set_page_config(layout="wide")

pages = [
    st.Page("reports.py", title="Dashboard"),
    st.Page("analysis.py", title="Analysis"),
]

pg = st.navigation(pages, position="top")
pg.run()
