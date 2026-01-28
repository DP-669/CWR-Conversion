import streamlit as st
import pandas as pd
from datetime import datetime
from cwr_engine import generate_cwr_content

st.set_page_config(page_title="Sync-Curator CWR Tool", page_icon="🎵")
st.title("Lumina CWR Generator")

uploaded_file = st.file_uploader("Upload Metadata CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"File loaded: {len(df)} tracks detected.")
    
    with st.expander("Preview & Column Check"):
        st.write(df.head())
        # Show which columns were detected
        st.info("The engine will auto-map columns like 'Work Title' to 'Title'.")

    if st.button("Generate Validated CWR"):
        try:
            cwr_output = generate_cwr_content(df)
            filename = f"LUMINA_ICE_{datetime.now().strftime('%Y%m%d')}.V21"
            
            st.download_button(
                label="📥 Download .V21 File",
                data=cwr_output,
                file_name=filename,
                mime="text/plain"
            )
            st.success("Generation Complete.")
        except Exception as e:
            st.error(f"Error: {e}")
