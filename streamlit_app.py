# streamlit_app.py
import streamlit as st
import pandas as pd
from cwr_engine import CWREngine

st.set_page_config(page_title="redCola CWR Factory", layout="wide")
st.title("🎵 redCola CWR Converter")

file = st.file_uploader("Upload Source CSV", type="csv")

if file:
    df = pd.read_csv(file)
    engine = CWREngine()
    output = []
    
    # 1. Start Envelope
    output.append(engine.make_hdr())
    output.append(engine.make_grh())
    
    # 2. Process Works
    for _, row in df.iterrows():
        # Using the new function name that handles complex splits
        output.append(engine.generate_work_block(row))
    
    # 3. Close Envelope
    output.append(engine.make_trl())
    
    final_text = "\n".join(output)
    st.download_button("Download Production CWR", final_text, "bulk_registration.txt")
    st.text_area("Live Review", final_text, height=400)
