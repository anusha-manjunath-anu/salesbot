
import streamlit as st

st.set_page_config(page_title="Meeting Suite", layout="wide")

st.sidebar.title("🧠 Navigation")
st.sidebar.markdown("---")
selected_page = st.sidebar.radio("Choose a section:", ["🧑‍💼 Meeting Assistant", "📊 Dashboard", "📰 Sales News"])

if selected_page == "🧑‍💼 Meeting Assistant":
    from meeting_assistant import main as run_meeting
    run_meeting()
elif selected_page == "📊 Dashboard":
    from dashboard import main as run_dashboard
    run_dashboard()
elif selected_page == "📰 Sales News":
    from sales_news import main as run_news
    run_news()
