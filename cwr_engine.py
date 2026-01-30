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

        # --- PUBLISHER LOOP ---
        for p_idx in range(1, 4):
            p_name = row.get(f'PUBLISHER {p_idx}: Name')
            if pd.isna(p_name): continue
            
            p_data = get_pub_data(p_name)
            p_share_pr = format_share(row.get(f'PUBLISHER {p_idx}: Collection Performance Share %'))
            p_share_mr = format_share(row.get(f'PUBLISHER {p_idx}: Collection Mechanical Share %'))
            
            # SPU 1: Original
            spu = CwrLine("SPU")
            spu.write(3, f"{t_seq:08d}")
            spu.write(11, f"{rec_seq:08d}")
            spu.write(19, f"{p_idx:02d}") # Chain ID
            spu.write(21, f"00000000{p_idx}")
            spu.write(30, p_data['name'], 45)
            spu.write(76, "E") 
            spu.write(87, p_data['ipi'], 11, True)
            spu.write(112, "021") 
            spu.write(115, p_share_pr, 5)
            spu.write(120, "021") 
            spu.write(123, p_share_mr, 5)
            spu.write(128, "   ") 
            spu.write(131, "03300") 
            spu.write(137, "N")
            spu.write(166, p_data['agreement'], 14)
            spu.write(180, "PG")
            lines.append(str(spu))
            rec_seq += 1
            
            # SPU 2: Lumina
            spu_l = CwrLine("SPU")
            spu_l.write(3, f"{t_seq:08d}")
            spu_l.write(11, f"{rec_seq:08d}")
            spu_l.write(19, f"{p_idx:02d}") # Same Chain
            spu_l.write(21, "000000012")
            spu_l.write(30, LUMINA_CONFIG['name'], 45)
            spu_l.write(76, "SE")
            spu_l.write(87, LUMINA_CONFIG['ipi'], 11, True)
            spu_l.write(112, "052") 
            spu_l.write(115, "00000") 
            spu_l.write(120, "033") 
            spu_l.write(123, "00000") 
            spu_l.write(128, "033") 
            
            # FIX: Zero Share for Lumina SPU (Matches Official)
            spu_l.write(131, "00000") 
            
            spu_l.write(137, "N")
            spu_l.write(166, p_data['agreement'], 14)
            spu_l.write(180, "PG")
            lines.append(str(spu_l))
            rec_seq += 1
            
            # SPT
            spt = CwrLine("SPT")
            spt.write(3, f"{t_seq:08d}")
            spt.write(11, f"{rec_seq:08d}")
            spt.write(19, "000000012") 
            
            # FIX: 6-Space Gap (Pos 28-33) - Writes start at 34? 
            # Wait, Pos 28 (1-based) is Index 27?
            # Standard SPT: Pub ID at 20 (Len 9) -> Ends 28. 
            # Share 1 at 30 (Len 5)? 
            # Let's trust the Geometry check from diff analysis:
            # "Off: ...012      01650..." -> 6 spaces.
            # ID ends at index 27 (start 19+8?). 000000012 is 9 chars.
            # 19 + 9 = 28. 
            # 28 + 6 spaces = 34.
            spt.write(34, p_share_pr, 5)
            spt.write(39, p_share_mr, 5)
            spt.write(44, "03300")
            spt.write(49, "I")
            spt.write(50, LUMINA_CONFIG['territory'])
            spt.write(55, "001")
            lines.append(str(spt))
            rec_seq += 1
            
            pub_map[p_data['name']] = {"idx": p_idx, "agreement": p_data['agreement'], "orig": p_data}

        # --- WRITER LOOP ---
        for w_idx in range(
