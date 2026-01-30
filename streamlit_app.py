import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Import Modules
from cwr_engine import generate_cwr_content
from cwr_validator import CWRValidator

st.set_page_config(page_title="Lumina CWR Suite", page_icon="🎵", layout="wide")

st.title("Lumina CWR Suite")
st.markdown("---")

# TABS: The user can switch between creating and checking
tab1, tab2 = st.tabs(["🚀 Generator (CSV to CWR)", "🛡️ Validator (Check CWR)"])

# ==============================================================================
# TAB 1: GENERATOR (Your existing logic, preserved)
# ==============================================================================
with tab1:
    st.header("Generate CWR v2.1")
    uploaded_file = st.file_uploader("Upload Metadata CSV", type="csv", key="gen_upload")

    if uploaded_file:
        # Header Detection Logic (Preserved from previous version)
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
        
        with st.expander("Preview Data"):
            st.write(df.head())

        if st.button("Generate Validated CWR", key="gen_btn"):
            try:
                cwr_output = generate_cwr_content(df)
                filename = f"LUMINA_ICE_{datetime.now().strftime('%Y%m%d')}.V21"
                
                st.download_button(
                    label="📥 Download .V21 File",
                    data=cwr_output,
                    file_name=filename,
                    mime="text/plain"
                )
                st.success("CWR Generated Successfully!")
                
                # Optional: Auto-validate the output immediately
                st.info("💡 Tip: You can download this, then upload it in the 'Validator' tab to double-check.")
                
            except Exception as e:
                st.error(f"Generation Failed: {str(e)}")

# ==============================================================================
# TAB 2: VALIDATOR (The New Gatekeeper)
# ==============================================================================
with tab2:
    st.header("Validate CWR v2.1")
    st.markdown("Checks for: `Syntax`, `Mandatory Fields`, `Hierarchy`, `Record Counts`.")
    
    val_file = st.file_uploader("Upload .V21 or .TXT CWR File", type=["v21", "txt"], key="val_upload")
    
    if val_file:
        # Read file as string
        stringio = io.StringIO(val_file.getvalue().decode("latin-1")) # CWR is usually Latin-1 or ASCII
        file_content = stringio.read()
        
        if st.button("Run Inspection", key="val_btn"):
            validator = CWRValidator()
            report, stats = validator.process_file(file_content)
            
            # --- DASHBOARD ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Lines", stats["lines_read"])
            col2.metric("Transactions (Works)", stats["transactions"])
            col3.metric("Errors Found", len(report))
            
            # --- TRAFFIC LIGHT SYSTEM ---
            if len(report) == 0:
                st.success("✅ PASSED. No structural errors found.")
            else:
                st.error(f"❌ FAILED. Found {len(report)} issues.")
                
                # Format Report for Dataframe
                df_report = pd.DataFrame(report)
                
                # Visual Priority
                def highlight_row(row):
                    if row.level == 'CRITICAL': return ['background-color: #ffcccc']*len(row)
                    if row.level == 'ERROR': return ['background-color: #ffeeba']*len(row)
                    return ['']*len(row)

                st.table(df_report)
