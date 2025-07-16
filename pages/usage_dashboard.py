import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from usage_logger import log_usage, read_logs

# ------------------------- 🔐 ACCESS CONTROL -------------------------
AUTH_USERS = {
    "admin": "super@Secret!987",
    "daniel": "Turbo@123#"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 Login Required")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in AUTH_USERS and AUTH_USERS[username] == password:
            st.session_state.logged_in = True
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("❌ Incorrect username or password.")

if not st.session_state.logged_in:
    login()
    st.stop()

# ------------------------- ✅ MAIN DASHBOARD -------------------------
st.set_page_config(page_title="Usage Dashboard", layout="wide")
st.title("📊 Usage Dashboard")
st.markdown("Monitor anonymous usage trends for the Sales Analyzer app.")

log_usage("usage_dashboard_opened")

# ------------------------- 📥 LOAD USAGE LOGS -------------------------
logs_df = read_logs()

if logs_df.empty:
    st.warning("⚠️ No usage data found.")
    st.stop()

# Convert Timestamp to datetime
logs_df["Timestamp"] = pd.to_datetime(logs_df["Timestamp"], errors="coerce")

# ------------------------- 🔍 FILTERS -------------------------
st.markdown("### 🔍 Filters")
col1, col2 = st.columns(2)

with col1:
    selected_event = st.selectbox("Event Type", ["All"] + sorted(logs_df["Event"].unique()))

with col2:
    date_range = st.date_input("Date Range", value=[], key="date_range")

filtered_df = logs_df.copy()
if selected_event != "All":
    filtered_df = filtered_df[filtered_df["Event"] == selected_event]

if isinstance(date_range, (list,tuple)) and len(date_range) == 2:
    start, end = date_range
    filtered_df = filtered_df[
        (filtered_df["Timestamp"].dt.date >= start) &
        (filtered_df["Timestamp"].dt.date <= end)
    ]

# ------------------------- 📈 SUMMARY METRICS -------------------------
st.markdown("### 📌 Event Summary")
event_counts = filtered_df["Event"].value_counts().reset_index()
event_counts.columns = ["Event", "Count"]
st.dataframe(event_counts, use_container_width=True)

# ------------------------- 📊 TIMELINE CHART -------------------------
st.markdown("### 📆 Daily Activity")
daily_counts = filtered_df.groupby(filtered_df["Timestamp"].dt.date).size()

if not daily_counts.empty:
    fig, ax = plt.subplots()
    daily_counts.plot(kind="bar", ax=ax)
    ax.set_ylabel("Event Count")
    ax.set_xlabel("Date")
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
else:
    st.info("No events in the selected date range.")

# ------------------------- 📋 RAW LOGS -------------------------
st.markdown("### 🧾 Raw Logs")
st.dataframe(
    filtered_df[["Timestamp", "Event", "Metadata"]].sort_values(by="Timestamp", ascending=False),
    use_container_width=True
)

# ------------------------- 🚪 LOGOUT -------------------------
st.markdown("---")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()
