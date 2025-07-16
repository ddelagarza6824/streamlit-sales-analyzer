
#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime
import io
from pathlib import Path
import traceback
from usage_logger import log_usage

# For testing locally; disable logging if secrets are unavailable
try:
    _ = st.secrets["google_sheets"]
except Exception:
    def log_usage(event, metadata=None):
        pass

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Sales Analyzer",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ------------------ CUSTOM CSS ------------------
st.markdown("""
    <style>
    .row_heading.level0, .blank {display:none}
    .stApp {background-color: #f7f9fa;}
    h1, h2, h3 {color: #0e1117;}
    .stButton>button {background-color: #4CAF50; color: white;}
    .main {padding-top: 2rem;}
    .upload-box {
        border: 2px dashed #ccc;
        padding: 2rem;
        border-radius: 10px;
        background-color: #f9f9f9;
    }
    .tips-box {
        background-color: #eef6ff;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        font-size: 0.95rem;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------ TITLE ------------------
st.markdown("## 📊 Sales Analyzer")

# ------------------ DEMO MODE ------------------
use_demo = st.sidebar.checkbox("🔧 Demo Mode (use sample data)", value=False)

# ------------------ FILE UPLOAD + WELCOME ------------------
if use_demo:
    sample_path = Path("sample.csv")
    if sample_path.exists():
        with sample_path.open("rb") as f:
            uploaded_file = io.BytesIO(f.read())
            uploaded_file.name = "sample.csv"  # mimic file_uploader
            st.success("📂 Loaded sample.csv in Demo Mode.")
    else:
        st.error("⚠️ sample.csv not found. Please add it to the project directory.")
        uploaded_file = None
else:
    uploaded_file = st.file_uploader("Upload your sales CSV file", type=["csv"])

if not uploaded_file:
    st.markdown("### 👋 Welcome to Sales Analyzer!")
    st.markdown("""
    This tool helps you explore, filter, and export your sales data with ease.
    - 📤 Upload a `.csv` file with columns like `Sales Rep`, `Client`, `Deal Size`, `Date`, and `Status`.
    - 📊 Instantly get metrics like revenue, win rate, and deal insights.
    - 💾 Export results to CSV or PNG for reporting.
    """)
    st.markdown("---")
    st.markdown('<div class="upload-box"></div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="tips-box">
            ✅ <b>Tips:</b><br>
            • File must be a CSV with headers<br>
            • Max size: 200MB<br>
            • We don’t store or share your data<br>
        </div>
    """, unsafe_allow_html=True)

    if Path("sample.csv").exists():
        with open("sample.csv", "rb") as f:
            st.download_button("📄 Download sample CSV", f, file_name="sample.csv", mime="text/csv")
# ------------------ MAIN APP ------------------
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [col.strip() for col in df.columns]
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Deal Size'] = pd.to_numeric(df['Deal Size'], errors='coerce')
        df.dropna(subset=['Date', 'Deal Size'], inplace=True)

        st.success("✅ File loaded and cleaned.")
        log_usage("file_uploaded")

        # ------------------ FILTERS ------------------
        st.sidebar.header("🧰 Filter Options")
        if "rep_filter" not in st.session_state:
            st.session_state["rep_filter"] = "All"
        if "status_filter" not in st.session_state:
            st.session_state["status_filter"] = "Closed"
        if "start_date" not in st.session_state:
            st.session_state["start_date"] = None
        if "end_date" not in st.session_state:
            st.session_state["end_date"] = None

        sales_reps = df['Sales Rep'].dropna().unique().tolist()
        selected_rep = st.sidebar.selectbox(
            "Sales Rep:",
            ["All"] + sales_reps,
            index=(["All"] + sales_reps).index(st.session_state["rep_filter"])
        )
        st.session_state["rep_filter"] = selected_rep

        status_options = ["Closed", "Lost", "Both"]
        selected_status = st.sidebar.selectbox(
            "Deal Status:",
            status_options,
            index=status_options.index(st.session_state["status_filter"])
        )
        st.session_state["status_filter"] = selected_status

        start_date = st.sidebar.date_input("Start Date", value=st.session_state["start_date"])
        end_date = st.sidebar.date_input("End Date", value=st.session_state["end_date"])
        st.session_state["start_date"] = start_date
        st.session_state["end_date"] = end_date

        if st.sidebar.button("🔄 Reset Filters"):
            st.session_state.clear()
            st.rerun()

        # ------------------ FILTER APPLICATION ------------------
        filtered_df = df.copy()
        if st.session_state["rep_filter"] != "All":
            filtered_df = filtered_df[filtered_df['Sales Rep'] == st.session_state["rep_filter"]]
        if st.session_state["status_filter"] != "Both":
            filtered_df = filtered_df[filtered_df['Status'].str.lower() == st.session_state["status_filter"].lower()]
        if st.session_state["start_date"]:
            filtered_df = filtered_df[filtered_df['Date'] >= pd.to_datetime(st.session_state["start_date"])]
        if st.session_state["end_date"]:
            filtered_df = filtered_df[filtered_df['Date'] <= pd.to_datetime(st.session_state["end_date"])]

        # ------------------ SALES SUMMARY ------------------
        st.markdown("### 📈 Sales Summary")
        closed_deals = filtered_df[filtered_df['Status'].str.lower() == 'closed']
        lost_deals = filtered_df[filtered_df['Status'].str.lower() == 'lost']

        if not closed_deals.empty:
            total_revenue = closed_deals['Deal Size'].sum()
            st.metric("💰 Total Revenue (Closed Deals)", f"${total_revenue:,.2f}")

            st.subheader("📋 Detailed Deals Closed")
            st.dataframe(closed_deals[['Sales Rep', 'Client', 'Deal Size', 'Date']].sort_values(by='Sales Rep'), hide_index=True)

            st.subheader("📦 Revenue, Deal Count, Clients per Rep")
            rep_stats = closed_deals.groupby("Sales Rep").agg(
                Revenue=("Deal Size", "sum"),
                Deals=("Deal Size", "count"),
                Clients=("Client", lambda x: ", ".join(sorted(x.unique())))
            ).reset_index()
            rep_stats["Revenue"] = rep_stats["Revenue"].map("${:,.2f}".format)
            st.dataframe(rep_stats, hide_index=True)

            win_rate = len(closed_deals) / len(filtered_df)
            st.metric("✅ Win Rate", f"{win_rate:.2%}")

            monthly_df = closed_deals.groupby(closed_deals['Date'].dt.to_period('M'))['Deal Size'].sum().reset_index()
            monthly_df.columns = ['Month', 'Revenue']
            monthly_df['Month'] = monthly_df['Month'].astype(str)
            monthly_df['Revenue'] = monthly_df['Revenue'].map('${:,.2f}'.format)

            st.subheader("📅 Monthly Revenue Breakdown")
            st.dataframe(monthly_df, hide_index=True)

            st.subheader("📊 Deals per Sales Rep Chart")
            deals_per_rep = closed_deals['Sales Rep'].value_counts().reset_index()
            deals_per_rep.columns = ["Sales Rep", "Deals Closed"]

            fig, ax = plt.subplots()
            deals_per_rep.set_index("Sales Rep")["Deals Closed"].plot(kind='bar', ax=ax, color='#4CAF50')
            ax.set_ylabel('Number of Deals')
            ax.set_xlabel('Sales Rep')
            plt.xticks(rotation=0)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("No closed deals found.")

        if not lost_deals.empty:
            st.subheader("❌ Lost Deals")
            st.dataframe(lost_deals[['Sales Rep', 'Client', 'Deal Size', 'Date']], hide_index=True)

        st.subheader("📤 Export Options")
        if not closed_deals.empty:
            closed_csv = closed_deals.to_csv(index=False).encode('utf-8')
            st.download_button("📄 Download Closed Deals CSV", closed_csv, "closed_deals.csv", "text/csv")

            monthly_csv = monthly_df.to_csv(index=False).encode('utf-8')
            st.download_button("📊 Download Monthly Revenue CSV", monthly_csv, "monthly_revenue.csv", "text/csv")

            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            st.download_button("🖼️ Download Chart as PNG", buf.getvalue(), "deals_chart.png", "image/png")

        st.subheader("💾 Manual File Export")
        export_folder = st.text_input("Folder path:", value=os.getcwd())
        base_name = st.text_input("File base name:", value=f"export_{datetime.datetime.now():%Y%m%d_%H%M%S}")
        if st.button("Save Files Locally"):
            try:
                os.makedirs(export_folder, exist_ok=True)
                closed_deals.to_csv(os.path.join(export_folder, f"{base_name}_closed.csv"), index=False)
                monthly_df.to_csv(os.path.join(export_folder, f"{base_name}_monthly.csv"), index=False)
                fig.savefig(os.path.join(export_folder, f"{base_name}_chart.png"))
                st.success("✅ Files saved successfully.")
            except Exception as e:
                st.error(f"❌ Export failed: {e}")

    except Exception as e:
        st.error("🚨 Error loading file:")
        st.text(traceback.format_exc())
else:
    st.info("Upload a CSV file to begin.")
