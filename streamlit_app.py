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
    with col2:
        st.info(f"Next File: CW{datetime.now().strftime('%y')}{seq_num:04d}LUM_319.V22")

    uploaded_file = st.file_uploader("Upload Metadata CSV", type="csv", key="gen_upload")

    if uploaded_file:
        try:
            # Header Detection Logic
            df_raw = pd.read_csv(uploaded_file, header=None)
            header_row_index = 0
            for i, row in df_raw.head(20).iterrows():
                row_text = row.astype(str).str.lower().tolist()
                if any('title' in x for x in row_text) or any('song' in x for x in row_text):
                    header_row_index = i
                    break
            
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, header=header_row_index)
            
            st.success(f"File loaded. Header detected at Row {header_row_index + 1}.")
            
            if st.button("Generate CWR File", key="gen_btn"):
                cwr_output = generate_cwr_content(df)
                
                # Naming Convention: CW + Year(2) + Seq(4) + Sender(3) + _ + Recipient(3) + .V22
                yy = datetime.now().strftime('%y')
                seq_str = f"{seq_num:04d}"
                filename = f"CW{yy}{seq_str}LUM_319.V22"
                
                st.download_button(
                    label=f"📥 Download {filename}",
                    data=cwr_output,
                    file_name=filename,
                    mime="text/plain"
                )
                st.success(f"Generated {filename}! Switch to the Validator tab to verify it.")
                
        except Exception as e:
            st.error(f"Generation Failed: {str(e)}")

# ==============================================================================
# TAB 2: VALIDATOR
# ==============================================================================
with tab2:
    st.header("Validate CWR")
    val_file = st.file_uploader("Upload .V21, .V22 or .TXT", type=["v21", "v22", "txt"], key="val_upload")
    
    if val_file:
        # Decode file safely
        stringio = io.StringIO(val_file.getvalue().decode("latin-1"))
        file_content = stringio.read()
        
        if st.button("Run Inspection", key="val_btn"):
            validator = CWRValidator()
            report, stats = validator.process_file(file_content)
            
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
