import streamlit as st
import pandas as pd
from datetime import datetime
import io
import zipfile
import re

# ==============================================================================
# EMBEDDED VALIDATOR (Forces Update / Bypasses Cache)
# ==============================================================================
class DirectValidator:
    def process_file(self, content):
        # Normalize line endings to ensure we don't count empty lines
        lines = content.replace('\r\n', '\n').split('\n')
        lines = [l for l in lines if len(l.strip()) > 0]
        
        report = []
        stats = {"lines_read": len(lines), "transactions": 0}
        
        curr_work = None
        has_w = False
        has_p = False
        
        # WE NOW SUPPORT BOTH REV (Legacy) AND NWR (New Standard)
        TRANS_TAGS = ["REV", "NWR"]

        for i, line in enumerate(lines):
            l_num = i + 1
            if len(line) < 3: continue
            
            rec = line[0:3]
            
            # 1. TRANSACTION LOGIC
            # If we hit a new transaction or trailer, validate the PREVIOUS work
            if rec in TRANS_TAGS or rec == "GRT" or rec == "TRL":
                if curr_work:
                    if not has_w:
                        report.append({"level": "CRITICAL", "line": l_num-1, "message": f"WORK '{curr_work}' HAS NO WRITERS.", "content": ""})
                    if not has_p:
                        report.append({"level": "CRITICAL", "line": l_num-1, "message": f"WORK '{curr_work}' HAS NO PUBLISHERS.", "content": ""})
                
                # Start New Work
                if rec in TRANS_TAGS:
                    # Title is always at pos 19-79
                    curr_work = line[19:79].strip() 
                    has_w = False
                    has_p = False
                    stats["transactions"] += 1
            
            # 2. COMPONENT CHECKS
            if rec == "SWR": has_w = True
            if rec == "SPU": has_p = True
            
            # 3. SYNTAX CHECKS
            
            # A. Field-Aware NAN check (Masking Title)
            line_check = line
            if rec in TRANS_TAGS:
                line_check = line[:19] + (" " * 60) + line[79:]
            
            if re.search(r'(?<!\w)NAN(?!\w)', line_check):
                report.append({"level": "ERROR", "line": l_num, "message": "Syntax Fail: Standalone 'NAN' found in data field.", "content": line})
            
            # B. Anchor Point Check (ORI at 142)
            if rec in TRANS_TAGS:
                if len(line) < 145 or line[142:145] != "ORI":
                    report.append({"level": "ERROR", "line": l_num, "message": f"Alignment Fail: '{rec}' record missing 'ORI' at pos 142.", "content": line})
            
            # C. IPI Padding Check
            if rec == "SWR":
                ipi = line[115:126].strip()
                if ipi != "" and not re.match(r'^\d{11}$', ipi):
                    report.append({"level": "ERROR", "line": l_num, "message": f"Padding Fail: IPI '{ipi}' is not 11 digits.", "content": line})

        return report, stats

# ==============================================================================
# MAIN APP
# ==============================================================================
try:
    from cwr_engine import generate_cwr_content
except ImportError as e:
    st.error(f"SYSTEM ERROR: cwr_engine.py not found. {e}")
    st.stop()

st.set_page_config(page_title="Lumina CWR Suite", page_icon="🎵", layout="wide")
st.title("Lumina CWR Suite")

tab1, tab2 = st.tabs(["🚀 Generator", "🛡️ Validator"])

# --- TAB 1: GENERATOR ---
with tab1:
    st.header("CWR Generator")
    col1, col2 = st.columns(2)
    with col1:
        seq = st.number_input("File Sequence", min_value=1, value=1)
    
    filename = f"CW{datetime.now().strftime('%y')}{seq:04d}LUM_319.V22"
    with col2: st.info(f"Generating: {filename}")

    # iPad Fix: Removed type validation to allow selection
    file = st.file_uploader("Upload Metadata CSV") 
    
    if file:
        try:
            # Universal Header Detection
            df_preview = pd.read_csv(file, header=None, nrows=20)
            h_idx = -1
            MARKERS = ["TRACK: TITLE", "LIBRARY: NAME", "SOURCEAUDIO ID", "FILENAME", "TITLE"]
            
            for i, row in df_preview.iterrows():
                row_str = row.astype(str).str.cat(sep=" ").upper()
                if any(m in row_str for m in MARKERS):
                    h_idx = i; break
            
            if h_idx == -1:
                st.error("Error: Schema not recognized. Ensure CSV contains 'TRACK: TITLE', 'SourceAudio ID', or 'Title'.")
            else:
                file.seek(0)
                df = pd.read_csv(file, header=h_idx)
                if st.button("Generate & Validate"):
                    cwr = generate_cwr_content(df)
                    st.success("File Generated.")
                    
                    # ZIP Wrapper
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, "w") as zf: zf.writestr(filename, cwr)
                    
                    st.download_button(
                        label="📦 Download ZIP (Safe Mode)",
                        data=buf.getvalue(),
                        file_name=f"{filename}.zip",
                        mime="application/zip"
                    )
        except Exception as e:
            st.error(f"Critical Failure: {e}")

# --- TAB 2: VALIDATOR ---
with tab2:
    st.header("CWR Validator")
    st.caption("iPad Tip: If your file is greyed out, it means iOS doesn't recognize the extension. Try dragging and dropping the file here.")
    
    # iPad Fix: Removed type=['V22'] so iOS doesn't grey out the file
    val_file = st.file_uploader("Check existing CWR") 
    
    if val_file:
        try:
            content = val_file.getvalue().decode("latin-1")
            
            if st.button("Run Inspection"):
                # Use the embedded class to ensure latest logic
                validator = DirectValidator()
                rep, stats = validator.process_file(content)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Lines Read", stats["lines_read"])
                c2.metric("Transactions Found", stats["transactions"])
                c3.metric("Issues", len(rep))
                
                if stats["transactions"] == 0:
                    st.warning("⚠️ No transactions found. Did you upload a valid CWR file?")
                    st.code(content[:500], language="text") # Debug preview
                
                if not rep and stats["transactions"] > 0: 
                    st.success("✅ Syntax Valid.")
                elif len(rep) > 0: 
                    st.error(f"Found {len(rep)} issues.")
                    for item in rep:
                        st.write(f"Line {item['line']} [{item['level']}]: {item['message']}")
                        st.code(item['content'])
        except Exception as e:
            st.error(f"Error reading file: {e}")
