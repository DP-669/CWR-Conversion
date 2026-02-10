import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Import Modules
try:
    from cwr_engine import generate_cwr_content
    from cwr_validator import CWRValidator
except ImportError as e:
    st.error(f"CRITICAL ERROR: Missing Modules. {e}")
    st.stop()

st.set_page_config(page_title="Lumina CWR Suite", page_icon="🎵", layout="wide")

st.title("Lumina CWR Suite (ICE/PRS)")
st.markdown("---")

tab1, tab2 = st.tabs(["🚀 Generator", "🛡️ Validator"])

# ==============================================================================
# TAB 1: GENERATOR
# ==============================================================================
with tab1:
    st.header("Generate CWR v2.2")
    
    col1, col2 = st.columns(2)
    with col1:
        seq_num = st.number_input("Sequence Number (0001, 0002...)", min_value=1, max_value=9999, value=1, format="%d")
    
    # Logic to generate the correct filename dynamically
    current_year_short = datetime.now().strftime('%y')
    filename_base = f"CW{current_year_short}{seq_num:04d}LUM_319.V22"
    
    with col2:
        st.info(f"Target Filename: {filename_base}")

    uploaded_file = st.file_uploader("Upload Metadata CSV", type="csv", key="gen_upload")

    if uploaded_file:
        try:
            # 1. READ FILE TO DETECT HEADER
            df_raw = pd.read_csv(uploaded_file, header=None)
            header_row_index = -1
            
            # Scan first 20 rows for "TRACK: TITLE" or similar
            for i, row in df_raw.head(20).iterrows():
                row_str = row.astype(str).str.cat(sep=" ").upper()
                if "TRACK: TITLE" in row_str or "TRACK TITLE" in row_str or "LIBRARY: NAME" in row_str:
                    header_row_index = i
                    break
            
            if header_row_index == -1:
                st.error("Could not detect header row in CSV. Ensure 'TRACK: Title' exists.")
            else:
                # 2. IMPORTANT: REWIND FILE POINTER BEFORE SECOND READ
                uploaded_file.seek(0)
                
                # 3. READ DATA WITH CORRECT HEADER
                df = pd.read_csv(uploaded_file, header=header_row_index)
                
                if st.button("Generate CWR File"):
                    cwr_content = generate_cwr_content(df)
                    
                    st.success("✅ CWR Generated Successfully!")
                    st.text_area("Preview (First 10 lines)", "\n".join(cwr_content.split("\n")[:10]), height=200)
                    
                    # DOWNLOAD BUTTON
                    st.download_button(
                        label="📥 Download CWR File (Ready for ICE)",
                        data=cwr_content,
                        file_name=filename_base, 
                        mime="application/octet-stream" 
                    )
                    
        except Exception as e:
            st.error(f"Error processing file: {e}")

# ==============================================================================
# TAB 2: VALIDATOR
# ==============================================================================
with tab2:
    st.header("Validate CWR File")
    st.markdown("Upload a `.V21`, `.V22`, or `.txt` file to check for syntax errors.")

    cwr_file = st.file_uploader("Upload CWR File", type=["V21", "V22", "txt", "dat"], key="val_upload")
    
    if cwr_file:
        try:
            # Decode file content
            stringio = io.StringIO(cwr_file.getvalue().decode("latin-1"))
            content = stringio.read()
            
            if st.button("Run Validation"):
                validator = CWRValidator()
                report, stats = validator.process_file(content)
                
                # --- DASHBOARD ---
                c1, c2, c3 = st.columns(3)
                c1.metric("Lines Read", stats["lines_read"])
                c2.metric("Works Found", stats["transactions"])
                c3.metric("Issues Found", len(report))
                
                if len(report) == 0:
                    st.success("✅ PASSED. File is clean and ready for submission.")
                else:
                    st.error(f"❌ FAILED. Found {len(report)} issues.")
                    
                    # Formatted Report
                    report_lines = []
                    report_lines.append(f"DIAGNOSTIC REPORT - {datetime.now()}")
                    report_lines.append(f"Total Issues: {len(report)}")
                    report_lines.append("-" * 60)
                    
                    for item in report:
                        report_lines.append(f"LINE {item['line']} [{item['level']}]: {item['message']}")
                        if item['content']:
                            report_lines.append(f"CONTENT: {item['content']}")
                        report_lines.append("-" * 20)
                    
                    report_text = "\n".join(report_lines)
                    
                    st.download_button(
                        label="📥 Download Diagnostic Report (.txt)",
                        data=report_text,
                        file_name="validation_errors.txt",
                        mime="text/plain"
                    )
                    
                    with st.expander("View Details On-Screen"):
                        st.text(report_text)
        except Exception as e:
            st.error(f"Error reading CWR file: {e}")
