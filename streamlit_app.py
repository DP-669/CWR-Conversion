import streamlit as st
import pandas as pd
from datetime import datetime
from cwr_engine import generate_cwr_content

st.set_page_config(page_title="Sync-Curator CWR Tool", page_icon="🎵")
st.title("Lumina CWR Generator (Restored)")

uploaded_file = st.file_uploader("Upload Metadata CSV", type="csv")

if uploaded_file:
    # --- RESET: SIMPLIFIED HEADER DETECTION ---
    # We read the raw file to find where the actual data starts.
    # This solves the issue of "Metadata Rows" causing UNKNOWN TITLE.
    
    df_raw = pd.read_csv(uploaded_file, header=None)
    header_row_index = 0
    
    # Simple Scan: Find the row that contains "Title" or "Song_Number"
    for i, row in df_raw.head(20).iterrows():
        row_text = row.astype(str).str.lower().tolist()
        if any('title' in x for x in row_text) or any('song' in x for x in row_text):
            header_row_index = i
            break
            
    # Reload with correct header
    uploaded_file.seek(0)
    df = pd.read_csv(uploaded_file, header=header_row_index)
    
    st.success(f"File loaded. Header detected at Row {header_row_index + 1}.")
    
    with st.expander("Preview Data (Verify Columns)"):
        st.write(df.head())
        # Visual Check for the user
        if 'Title' not in df.columns and 'Work Title' not in df.columns:
            st.error("⚠️ Warning: 'Title' column not found. Output may show 'UNKNOWN TITLE'. Check your CSV.")

    if st.button("Generate Validated CWR"):
        try:
            cwr_output = generate_cwr_content(df)
            
            filename = f"LUMINA_ICE_{datetime.now().strftime('%Y%m%d')}.V21"
            
            st.download_button(
                label="📥 Download Validated .V21 File",
                data=cwr_output,
                file_name=filename,
                mime="text/plain"
            )
            st.success("Generation Complete.")
            
        except Exception as e:
            st.error(f"Error: {e}")
