import streamlit as st
import pandas as pd
from datetime import datetime
# This line was the error. We are now pointing to the correct file name.
from cwr_generator import generate_cwr_content

st.set_page_config(page_title="Sync-Curator CWR Tool", page_icon="🎵")

st.title("Lumina CWR Generator")
st.markdown("### ICE-Validated V2.1 Conversion")

uploaded_file = st.file_uploader("Upload your Metadata CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"File loaded: {len(df)} tracks detected.")
    
    # Optional: Display a small preview to ensure columns are mapped
    with st.expander("Preview Uploaded Data"):
        st.write(df.head())

    if st.button("Finalize & Generate CWR"):
        try:
            # Call the engine from cwr_generator.py
            cwr_output = generate_cwr_content(df)
            
            # Generate filename with today's date
            datestamp = datetime.now().strftime("%Y%m%d")
            filename = f"LUMINA_ICE_{datestamp}.V21"
            
            st.download_button(
                label="📥 Download Validated .V21 File",
                data=cwr_output,
                file_name=filename,
                mime="text/plain"
            )
            st.balloons()
            st.success("CWR Generation Successful. Ready for ICE portal upload.")
            
        except Exception as e:
            st.error(f"Logic Error: {e}")
            st.info("Check that your CSV has 'Title', 'Song_Number', and 'Publisher' columns.")
