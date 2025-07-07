#!/usr/bin/env python
# coding: utf-8

# In[20]:

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime
import io
from pathlib import path

st.set_page_config(
    page_title="Sales Analyzer",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
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
st.caption("Upload your sales CSV file to begin.")

# ------------------ FILE UPLOAD ------------------
with st.container():
    st.markdown('<div class="upload-box">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(" ", type=["csv"], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    # ------------------ TIPS ------------------
    st.markdown("""
        <div class="tips-box">
            ✅ <b>Tips:</b><br>
            • File must be a CSV with headers<br>
            • Max size: 200MB<br>
            • We don’t store or share your data<br>
        </div>
    """, unsafe_allow_html=True)

    # Optional download sample CSV button
    sample_path = Path("sample.csv")
    if sample_path.exists():
        with open(sample_path, "rb") as f:
            st.download_button("📄 Download sample CSV", f, file_name="sample.csv", mime="text/csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [col.strip() for col in df.columns]
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Deal Size'] = pd.to_numeric(df['Deal Size'], errors='coerce')
        df.dropna(subset=['Date', 'Deal Size'], inplace=True)

        st.success("File loaded and cleaned.")

        # Sidebar Filters
        st.sidebar.header("🧰 Filter Options")
        sales_reps = df['Sales Rep'].dropna().unique().tolist()
        selected_rep = st.sidebar.selectbox("Sales Rep:", ["All"] + sales_reps)

        status_options = ["Closed", "Lost", "Both"]
        default_status = st.session_state.get("status_filter", "Closed")
        selected_status = st.sidebar.selectbox("Deal Status:", options=status_options, index=status_options.index(default_status))
        st.session_state["status_filter"] = selected_status

        start_date = st.sidebar.date_input("Start Date", value=None)
        end_date = st.sidebar.date_input("End Date", value=None)

        # Apply filters
        filtered_df = df.copy()
        if selected_rep != "All":
            filtered_df = filtered_df[filtered_df['Sales Rep'] == selected_rep]
        if selected_status != "Both":
            filtered_df = filtered_df[filtered_df['Status'].str.lower() == selected_status.lower()]
        if start_date:
            filtered_df = filtered_df[filtered_df['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            filtered_df = filtered_df[filtered_df['Date'] <= pd.to_datetime(end_date)]

        if filtered_df.empty:
            st.warning("No results found with these filters.")
        else:
            st.success(f"{len(filtered_df)} rows match your criteria.")

            # Sales Summary
            st.subheader("📈 Sales Summary")
            closed_deals = filtered_df[filtered_df['Status'].str.lower() == 'closed']
            lost_deals = filtered_df[filtered_df['Status'].str.lower() == 'lost']

            if not closed_deals.empty:
                total_revenue = closed_deals['Deal Size'].sum()
                st.metric("💰 Total Revenue (Closed Deals)", f"${total_revenue:,.2f}")

                # --- New Detailed Deals Table ---
                st.subheader("📋 Detailed Deals Closed")
                detailed_deals = closed_deals[['Sales Rep', 'Client', 'Deal Size', 'Date']].sort_values(by='Sales Rep')
                st.dataframe(detailed_deals, hide_index=True)

                # --- Revenue & Deal Count by Rep + Clients ---
                st.subheader("📦 Revenue, Deal Count, Clients per Rep")
                rep_stats = closed_deals.groupby("Sales Rep").agg(
                    Revenue=("Deal Size", "sum"),
                    Deals=("Deal Size", "count"),
                    Clients=("Client", lambda x: ", ".join(sorted(x.unique())))
                ).reset_index()
                rep_stats["Revenue"] = rep_stats["Revenue"].map("${:,.2f}".format)
                st.dataframe(rep_stats, hide_index=True)

                # --- Win Rate ---
                win_rate = len(closed_deals) / len(filtered_df)
                st.metric("✅ Win Rate", f"{win_rate:.2%}")

                # --- Monthly Revenue ---
                monthly_df = closed_deals.groupby(closed_deals['Date'].dt.to_period('M'))['Deal Size'].sum().reset_index()
                monthly_df.columns = ['Month', 'Revenue']
                monthly_df['Month'] = monthly_df['Month'].astype(str)
                monthly_df['Revenue'] = monthly_df['Revenue'].map('${:,.2f}'.format)

                st.subheader("📅 Monthly Revenue Breakdown")
                st.dataframe(monthly_df, hide_index=True)

                # --- Chart: Deals per Rep ---
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

            # Lost Deals Table
            if not lost_deals.empty:
                st.subheader("❌ Lost Deals")
                st.dataframe(lost_deals[['Sales Rep', 'Client', 'Deal Size', 'Date']], hide_index=True)

            # Export Options
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
                    st.success("Files saved successfully.")
                except Exception as e:
                    st.error(f"Export failed: {e}")
    except Exception as e:
        st.error(f"Error loading file: {e}")
else:
    st.info("Upload a CSV file to begin.")




# In[ ]:




