# streamlit_app.py
import streamlit as st
import pandas as pd
from cwr_engine import CWREngine

st.set_page_config(page_title="redCola CWR Factory", layout="wide")
st.title("🎵 redCola CWR Converter")
st.info("Upload your CSV. The system will apply 'Bible' logic for ICE/PRS registration.")

file = st.file_uploader("Upload CSV", type="csv")

if file:
    df = pd.read_csv(file)
    engine = CWREngine()
    
    # Assembly
    output = []
    output.append(engine.make_hdr())
    output.append(engine.make_grh())
    for _, row in df.iterrows():
        output.append(engine.make_nwr_block(row))
    output.append(engine.make_trl())
    
    final_text = "\n".join(output)
    
    st.download_button("Download CWR File", final_text, "registration.txt", "text/plain")
    st.text_area("File Preview", final_text, height=300)