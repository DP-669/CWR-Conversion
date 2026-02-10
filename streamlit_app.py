import streamlit as st
import pandas as pd
from datetime import datetime
import io
import zipfile

try:
    from cwr_engine import generate_cwr_content
    from cwr_validator import CWRValidator
except ImportError as e:
    st.error(f"SYSTEM ERROR: Logic components not found. {e}")
    st.stop()

st.set_page_config(page_title="Lumina CWR Suite", page_icon="🎵", layout="wide")
st.title("Lumina CWR Suite")

tab1, tab2 = st.tabs(["🚀 Generator", "🛡️ Validator"])

with tab1:
    st.header("CWR Generator")
    col1, col2 = st.columns(2)
    with col1:
        seq = st.number_input("File Sequence", min_value=1, value=1)
    
    filename = f"CW{datetime.now().strftime('%y')}{seq:04d}LUM_319.V22"
    with col2: st.info(f"Generating: {filename}")

    file = st.file_uploader("Upload Metadata CSV", type="csv")
    if file:
        try:
            df_preview = pd.read_csv(file, header=None, nrows=20)
            h_idx = -1
            MARKERS = ["TRACK: TITLE", "LIBRARY: NAME", "SOURCEAUDIO ID", "FILENAME", "TITLE"]
            for i, row in df_preview.iterrows():
                row_str = row.astype(str).str.cat(sep=" ").upper()
                if any(m in row_str for m in MARKERS):
                    h_idx = i; break
            
            if h_idx == -1:
                st.error("Error: Schema not recognized.")
            else:
                file.seek(0)
                df = pd.read_csv(file, header=h_idx)
                if st.button("Generate & Validate"):
                    cwr = generate_cwr_content(df)
                    st.success("File Generated.")
                    
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, "w") as zf: zf.writestr(filename, cwr)
                    
                    st.download_button(
                        label="📦 Download CWR ZIP (Safe Mode)",
                        data=buf.getvalue(),
                        file_name=f"{filename}.zip",
                        mime="application/zip"
                    )
        except Exception as e:
            st.error(f"Critical Failure: {e}")

with tab2:
    st.header("CWR Validator")
    val_file = st.file_uploader("Check existing CWR")
    if val_file:
        content = val_file.getvalue().decode("latin-1")
        if st.button("Run Inspection"):
            rep, stats = CWRValidator().process_file(content)
            st.metric("Transactions", stats["transactions"])
            if not rep: st.success("Syntax Valid.")
            else: st.error(f"Found {len(rep)} issues."); st.write(rep)
