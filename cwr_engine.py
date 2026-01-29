import pandas as pd
from datetime import datetime

# --- 1. CONFIGURATION & DATABASE ---
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

# --- 2. STRICT GEOMETRY ASSEMBLER ---
class CwrLine:
    """Constructs a fixed-width CWR line by placing data at exact indices."""
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

# --- 3. GENERATION LOGIC ---
def generate_cwr_content(df):
    lines = []
    now_d = datetime.now().strftime("%Y%m%d")
    now_t = datetime.now().strftime("%H%M%S")
    
    # HDR
    hdr = CwrLine("HDR")
    hdr.write(3, LUMINA_CONFIG['ipi'], 11, True)
    hdr.write(14, LUMINA_CONFIG['name'], 45)
    hdr.write(59, "01.10")
    hdr.write(64, now_d)
    hdr.write(72, now_t)
    hdr.write(78, now_d)
    hdr.write(98, "BACKBEAT") 
    lines.append(str(hdr))
    lines.append("GRHREV0000102.200000000001")

    for i, row in df.iterrows():
        t_seq = i 
        
        # ID Logic
        raw_id = row.get('Song_Number')
        if pd.isna(raw_id): raw_id = row.get('CODE: Song Code')
        if pd.isna(raw_id): raw_id = f"{int(row.get('TRACK: Number', 0)):07d}"
        submitter_id = raw_id
        
        # REV
        rev = CwrLine("REV")
        rev.write(3, f"{t_seq:08d}")
        rev.write(11, "00000000")
        rev.write(19, row.get('TRACK: Title', 'UNKNOWN'), 60)
        rev.write(81, submitter_id, 14)
        rev.write(95, row.get('CODE: ISWC', ''), 11)
        rev.write(106, "00000000") 
        rev.write(126, "UNC")
        rev.write(129, "000025") 
        rev.write(135, "Y")
        lines.append(str(rev))

        rec_seq = 1
        pub_map = {}

        # --- PUBLIS
