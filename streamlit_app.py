import streamlit as st
import pandas as pd
from datetime import datetime
# FIX: Imports from your correctly named file 'cwr_engine.py'
from cwr_engine import generate_cwr_content

st.set_page_config(page_title="Sync-Curator CWR Tool", page_icon="🎵")
st.title("Lumina CWR Generator")
st.markdown("### ICE-Validated V2.1 Conversion")

uploaded_file = st.file_uploader("Upload your Metadata CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"File loaded: {len(df)} tracks detected.")
    
    with st.expander("Preview Uploaded Data"):
        st.write(df.head())

    if st.button("Finalize & Generate CWR"):
        try:
            # Call the engine
            cwr_output = generate_cwr_content(df)
            
            # Generate filename
            datestamp = datetime.now().strftime("%Y%m%d")
            filename = f"LUMINA_ICE_{datestamp}.V21"
            
            st.download_button(
                label="📥 Download Validated .V21 File",
                data=cwr_output,
                file_name=filename,
                mime="text/plain"
            )
            st.success("CWR Generation Successful. Ready for ICE portal upload.")
            
        except Exception as e:
            st.error(f"Logic Error: {e}")
