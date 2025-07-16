import gspread
import datetime
import streamlit as st
import pandas as pd

def log_usage(event_type, metadata=None):
    """Logs an event with optional metadata to the 'streamlit log' Google Sheet."""
    try:
        gc = gspread.service_account_from_dict(st.secrets["google_sheets"])
        worksheet = gc.open("streamlit log").sheet1
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        metadata_str = "" if metadata is None else str(metadata)
        worksheet.append_row([timestamp, event_type, metadata_str])
    except Exception:
        pass  # Silently fail if secrets or logging fails

def read_logs():
    """Reads the full usage log as a pandas DataFrame."""
    try:
        gc = gspread.service_account_from_dict(st.secrets["google_sheets"])
        worksheet = gc.open("streamlit log").sheet1
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame(columns=["Timestamp", "Event", "Metadata"])
