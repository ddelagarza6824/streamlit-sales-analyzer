import streamlit as st
import pandas as pd
import ast
from usage_logger import log_usage, read_logs

# -------------------------
# 🔐 ACCESS CONTROL SECTION
# -------------------------

# Define allowed users and passwords
AUTH_USERS = {
    "admin": "super@Secret!987",
    "daniel": "Turbo@123#"
}

# Session state to track login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Login form
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

# Require login
if not st.session_state.logged_in:
    login()
    st.stop()

# -------------------------
# ✅ MAIN DASHBOARD SECTION
# -------------------------

# User ID from URL (optional)
user_id = st.query_params.get("user", "anonymous")

# Page setup
st.set_page_config(page_title="Usage Dashboard", layout="wide")
st.title("📊 Usage Dashboard")
st.markdown("Monitor how users interact with your Streamlit apps.")

# Log this access
log_usage("Usage Dashboard Opened", {"user": user_id})

# Load usage logs
logs_df = read_logs()

# Parse metadata safely
def extract_metadata_fields(df):
    def safe_parse(x):
        try:
            parsed = ast.literal_eval(x)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    df["Metadata_dict"] = df["User_ID"].apply(safe_parse)
    df["Sales Rep"] = df["Metadata_dict"].apply(lambda x: x.get("Sales Rep"))
    df["Filename"] = df["Metadata_dict"].apply(lambda x: x.get("filename"))
    df["Status"] = df["Metadata_dict"].apply(lambda x: x.get("Status"))
    df["User"] = df["Metadata_dict"].apply(lambda x: x.get("user"))
    return df

logs_df = extract_metadata_fields(logs_df)

if logs_df.empty:
    st.info("No usage data found.")
else:
    # Filters
    st.markdown("### 🔍 Filters")
    col1, col2 = st.columns(2)

    with col1:
        selected_event = st.selectbox("Filter by Event Type", ["All"] + sorted(logs_df["Event"].unique()))
    with col2:
        date_range = st.date_input("Filter by Date Range", [])

    filtered_df = logs_df.copy()

    if selected_event != "All":
        filtered_df = filtered_df[filtered_df["Event"] == selected_event]

    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df["Timestamp"] = pd.to_datetime(filtered_df["Timestamp"])
        filtered_df = filtered_df[
            (filtered_df["Timestamp"].dt.date >= start_date) &
            (filtered_df["Timestamp"].dt.date <= end_date)
        ]

    # Summary
    st.markdown("### 📈 Summary")
    event_counts = filtered_df["Event"].value_counts().reset_index()
    event_counts.columns = ["Event", "Count"]
    st.dataframe(event_counts, use_container_width=True)

    # Charts
    st.markdown("### 📊 Event Frequency")
    if not event_counts.empty:
        st.bar_chart(event_counts.set_index("Event"))

    if "Sales Rep" in filtered_df.columns and filtered_df["Sales Rep"].notna().any():
        rep_counts = filtered_df["Sales Rep"].value_counts().reset_index()
        rep_counts.columns = ["Sales Rep", "Count"]
        st.markdown("### 👤 Top Sales Reps (Filtered Events)")
        st.bar_chart(rep_counts.set_index("Sales Rep"))

    # Raw logs
    st.markdown("### 🧾 Raw Logs")
    display_cols = ["Timestamp", "Event", "User", "Filename", "Sales Rep", "Status"]
    st.dataframe(filtered_df[display_cols].sort_values(by="Timestamp", ascending=False), use_container_width=True)

# -------------------------
# 🚪 LOGOUT BUTTON
# -------------------------
st.markdown("---")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()






