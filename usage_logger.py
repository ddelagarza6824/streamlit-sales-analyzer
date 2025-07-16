import gspread
import datetime
import streamlit as st

def log_usage(event_type, metadata=None):
    """
    Logs an event with optional metadata to the 'streamlit log' Google Sheet.
    """
    try:
        gc = gspread.service_account_from_dict(st.secrets["google_sheets"])
        worksheet = gc.open("streamlit log").sheet1
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata_str = str(metadata) if metadata else ""
        worksheet.append_row([timestamp, event_type, metadata_str])
    except Exception as e:
        st.warning(f"⚠️ Failed to log usage: {e}")


        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata_str = str(metadata) if metadata else ""

        worksheet.append_row([timestamp, event_type, metadata_str])
    except Exception as e:
        st.warning(f"Failed to log usage: {e}")

def read_logs():
    """
    Reads the full usage log from the 'streamlit log' Google Sheet.

    Returns:
        pd.DataFrame: The log as a pandas DataFrame with columns [Timestamp, Event, Metadata]
    """
    import pandas as pd
    try:
        gc = gspread.service_account_from_dict(st.secrets["google_sheets"])
        worksheet = gc.open("streamlit log").sheet1
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"⚠️ Failed to read logs: {e}")
        return pd.DataFrame(columns=["Timestamp", "Event", "Metadata"])

