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

st.title("Lumina CWR Suite")
st.markdown("---")

tab1, tab2 = st.tabs(["🚀 Generator", "🛡️ Validator"])

# ==============================================================================
# TAB 1: GENERATOR
# ==============================================================================
with tab1:
    st.header("Generate CWR v2.1")
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
            
            if st.button("Generate CWR", key="gen_btn"):
                cwr_output = generate_cwr_content(df)
                filename = f"LUMINA_ICE_{datetime.now().strftime('%Y%m%d')}.V21"
                
                st.download_button(
                    label="📥 Download .V21",
                    data=cwr_output,
                    file_name=filename,
                    mime="text/plain"
                )
                st.success("Generated! Go to the Validator tab to check it.")
                
        except Exception as e:
            st.error(f"Generation Failed: {str(e)}")

# ==============================================================================
# TAB 2: VALIDATOR (Simplified: Download Only)
# ==============================================================================
with tab2:
    st.header("Validate CWR")
    val_file = st.file_uploader("Upload .V21 or .TXT", type=["v21", "txt"], key="val_upload")
    
    if val_file:
        stringio = io.StringIO(val_file.getvalue().decode("latin-1"))
        file_content = stringio.read()
        
        if st.button("Run Inspection", key="val_btn"):
            validator = CWRValidator()
            report, stats = validator.process_file(file_content)
            
            # --- DASHBOARD ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Lines Read", stats["lines_read"])
            col2.metric("Works Found", stats["transactions"])
            col3.metric("Errors Found", len(report))
            
            if len(report) == 0:
                st.success("✅ PASSED. File is clean.")
            else:
                st.error(f"❌ FAILED. Found {len(report)} issues.")
                
                # Create a formatted text report for analysis
                report_lines = []
                report_lines.append(f"DIAGNOSTIC REPORT - {datetime.now()}")
                report_lines.append(f"Total Errors: {len(report)}")
                report_lines.append("-" * 60)
                
                for item in report:
                    report_lines.append(f"LINE {item['line']} [{item['level']}]: {item['message']}")
                    report_lines.append(f"CONTENT: {item['content']}")
                    report_lines.append("-" * 20)
                
                report_text = "\n".join(report_lines)
                
                st.download_button(
                    label="📥 Download Diagnostic Report (.txt)",
                    data=report_text,
                    file_name="validation_errors.txt",
                    mime="text/plain"
                )
                st.info("Download this report and paste it into the chat for analysis.")
