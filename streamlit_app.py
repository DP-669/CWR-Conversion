import streamlit as st
import pandas as pd
from datetime import datetime
from cwr_engine import generate_cwr_content, normalize_columns

st.set_page_config(page_title="Sync-Curator CWR Tool", page_icon="🎵")
st.title("Lumina CWR Generator")

uploaded_file = st.file_uploader("Upload Metadata CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # Run the smart-mapper immediately to show user what we found
    mapped_df = normalize_columns(df.copy())
    
    st.success(f"File loaded: {len(df)} tracks.")
    
    with st.expander("✅ Verify Column Mapping"):
        st.write("We detected these columns from your file:")
        st.dataframe(mapped_df.head(3))
        
        # Safety Check
        required = ['Title', 'Song_Number', 'Publisher']
        missing = [col for col in required if col not in mapped_df.columns]
        if missing:
            st.error(f"⚠️ Warning: We could not find columns for: {', '.join(missing)}. Please check your CSV headers.")
        else:
            st.success("All required columns mapped successfully!")

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
        except Exception as e:
            st.error(f"Error: {e}")
