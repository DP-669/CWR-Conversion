import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
LUMINA_CONFIG = {
    "name": "LUMINA PUBLISHING UK",
    "ipi": "01254514077",
    "role": "SE",
    "territory": "0826"
}

PUBLISHER_DB = {
    "TARMAC": {"name": "TARMAC 1331 PUBLISHING", "ipi": "00356296239", "agreement": "6781310"},
    "PASHALINA": {"name": "PASHALINA PUBLISHING", "ipi": "00498578867", "agreement": "4316161"},
    "MANNY": {"name": "MANNY G MUSIC", "ipi": "00515125979", "agreement": "13997451"},
    "SNOOPLE": {"name": "SNOOPLE SONGS", "ipi": "00610526488", "agreement": "13990221"}
}

# --- CWR ASSEMBLER ---
class CwrLine:
    def __init__(self, record_type):
        self.buffer = [' '] * 512 
        self.write(0, record_type)
        
    def write(self, start, val, length=None, is_num=False):
        if pd.isna(val): val = ""
        s_val = str(val).strip().upper()
        if is_num:
            if s_val.endswith('.0'): s_val = s_val[:-2]
            s_val = ''.join(filter(str.isdigit, s_val))
            formatted = s_val.zfill(length) if length else s_val
        else:
            formatted = s_val.ljust(length) if length else s_val
            
        if length: formatted = formatted[:length]
        
        for i, char in enumerate(formatted):
            if start + i < len(self.buffer):
                self.buffer[start + i] = char
    
    def __str__(self):
        return "".join(self.buffer).rstrip()

def format_share(val):
    try:
        if pd.isna(val) or str(val).strip() == '': return "00000"
        return f"{int(round(float(val) * 100)):05d}"
    except: return "00000"

def get_pub_data(raw_name):
    raw = str(raw_name).upper()
    for key, data in PUBLISHER_DB.items():
        if key in raw: return data
    return {"name": raw_name[:45], "ipi": "00000000000", "agreement": "00000000"}

# --- GENERATION
