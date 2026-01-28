import streamlit as st
import pandas as pd
from datetime import datetime
from cwr_engine import generate_cwr_content, normalize_columns

st.set_page_config(page_title="Sync-Curator CWR Tool", page_icon="🎵")
st.title("Lumina CWR Generator")

uploaded_file = st.file_uploader("Upload Metadata CSV", type="csv")

if uploaded_file:
    # --- SMART LOADER: Detect Header Row ---
    # 1. Read the file without assuming a header
    df_raw = pd.read_csv(uploaded_file, header=None)
    
    # 2. Scan first 10 rows to find the real header (containing 'Title' and 'Publisher')
    header_idx = 0
    found_header = False
    
    for i, row in df_raw.head(10).iterrows():
        # Convert row to lowercase string for searching
        row_text = row.astype(str).str.lower().tolist()
        
        # Heuristic: If row has 'title' AND 'publisher' (or variants), it's the header
        has_title = any(x in str(row_text) for x in ['title', 'work title', 'track name'])
        has_pub = any(x in str(row_text) for x in ['publisher', 'copyright', 'label'])
        
        if has_title: # 'Publisher' check is optional as it might be missing in some exports
            header_idx = i
            found_header = True
            break
    
    # 3. Reload the dataframe using the detected header row
    uploaded_file.seek(0) # Reset file pointer
    df = pd.read_csv(uploaded_file, header=header_idx)
    
    # --- END SMART LOADER ---

    # Normalize columns immediately to verify mapping
    df = normalize_columns(df)
    
    st.success(f"File loaded successfully! (Header detected at Row {header_idx+1})")
    
    with st.expander("✅ Verify Data Preview"):
        st.write(df.head())
        
        # Check for Critical Columns
        required = ['Title', 'Song_Number']
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            st.error(f"⚠️ CRITICAL: Could not find columns: {', '.join(missing)}. output will contain 'UNKNOWN TITLE'.")
        else:
            st.info("Columns mapped correctly. Ready to generate.")

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
        except Exception as e:
            st.error(f"Error: {e}")
