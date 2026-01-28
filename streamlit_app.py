# streamlit_app.py
import streamlit as st
import pandas as pd
from cwr_engine import CWREngine

st.set_page_config(page_title="redCola Production CWR", layout="wide")
st.title("🎵 redCola Production CWR Factory")
st.markdown("Upload your Harvest Media CSV. The system handles all sequencing automatically.")

file = st.file_uploader("Upload Source CSV", type="csv")

if file:
    df = pd.read_csv(file)
    engine = CWREngine()
    output = []
    
    output.append(engine.make_hdr())
    output.append(engine.make_grh())
    
    for _, row in df.iterrows():
        output.append(engine.generate_work_block(row))
    
    output.append(engine.make_trl())
    
    final_text = "\n".join(output)
    st.download_button("Download Finished CWR", final_text, "registration.txt")
    st.text_area("Live Review", final_text, height=300)
    st.success(f"Processed {len(df)} tracks successfully.")
