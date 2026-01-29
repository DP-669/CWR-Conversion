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
    """Constructs a fixed-width CWR line by placing data at exact CWR 2.1/2.2 indices."""
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

# --- 3. HELPER FUNCTIONS ---
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

# --- 4. GENERATION LOGIC ---
def generate_cwr_content(df):
    lines = []
    now_d = datetime.now().strftime("%Y%m%d")
    now_t = datetime.now().strftime("%H%M%S")
    
    # HDR (Standard 2.2 Header)
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
        
        # ID Logic: Uses Song_Number or Track Number
        raw_id = row.get('Song_Number')
        if pd.isna(raw_id): raw_id = row.get('CODE: Song Code')
        if pd.isna(raw_id): raw_id = f"{int(row.get('TRACK: Number', 0)):07d}"
        submitter_id = raw_id
        
        # REV RECORD
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
            spu.write(19, "01")
            spu.write(21, f"00000000{p_idx}")
            spu.write(30, p_data['name'], 45)
            spu.write(76, "E") 
            spu.write(87, p_data['ipi'], 11, True)
            spu.write(112, "021") # PR Soc
            spu.write(115, p_share_pr, 5)
            spu.write(120, "021") # MR Soc
            spu.write(123, p_share_mr, 5)
            
            # GEOMETRY FIX 1: SR Society (3 chars) at 128 (Left empty as per Parity)
            spu.write(128, "   ") 
            
            # GEOMETRY FIX 1: SR Share (5 chars) at 131
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
            spu_l.write(19, "01")
            spu_l.write(21, "000000012")
            spu_l.write(30, LUMINA_CONFIG['name'], 45)
            spu_l.write(76, "SE")
            spu_l.write(87, LUMINA_CONFIG['ipi'], 11, True)
            spu_l.write(112, "052") 
            spu_l.write(115, "00000") 
            spu_l.write(120, "033") 
            spu_l.write(123, "00000") 
            spu_l.write(128, "   ") # SR Soc
            spu_l.write(131, "03300") # SR Share
            spu_l.write(137, "N")
            spu_l.write(166, p_data['agreement'], 14)
            spu_l.write(180, "PG")
            lines.append(str(spu_l))
            rec_seq += 1
            
            # SPT
            lines.append(f"SPT{t_seq:08d}{rec_seq:08d}{p_share_pr}{p_share_mr}03300I{LUMINA_CONFIG['territory']} 001")
            rec_seq += 1
            pub_map[p_data['name']] = {"idx": p_idx, "agreement": p_data['agreement'], "orig": p_data}

        # --- WRITER LOOP ---
        for w_idx in range(1, 4):
            w_last = row.get(f'WRITER {w_idx}: Last Name')
            if pd.isna(w_last): continue
            
            w_first = row.get(f'WRITER {w_idx}: First Name', '')
            w_ipi = row.get(f'WRITER {w_idx}: IPI')
            w_pr = format_share(row.get(f'WRITER {w_idx}: Collection Performance Share %'))
            
            # SWR
            swr = CwrLine("SWR")
            swr.write(3, f"{t_seq:08d}")
            swr.write(11, f"{rec_seq:08d}")
            swr.write(19, f"00000000{w_idx}")
            swr.write(28, w_last, 45)
            swr.write(73, w_first, 30)
            swr.write(104, "C ")
            swr.write(115, w_ipi, 11, True)
            
            # GEOMETRY FIX 2: PR Society at 126 (Required by Parity/Manual)
            swr.write(126, "021") 
            
            swr.write(129, w_pr, 5)
            swr.write(134, "099") # MR Soc
            swr.write(137, "00000")
            swr.write(142, "099") # SR Soc
            swr.write(145, "00000")
            swr.write(150, "N")
            lines.append(str(swr))
            rec_seq += 1
            
            # SWT
            lines.append(f"SWT{t_seq:08d}{rec_seq:08d}00000000{w_idx}{w_pr}00000000000000I2136 001")
            rec_seq += 1
            
            # PWR
            orig_pub_name = str(row.get(f'WRITER {w_idx}: Original Publisher')).upper()
            linked = next((v for k, v in pub_map.items() if k in orig_pub_name), None)
            
            if linked:
                pwr = CwrLine("PWR")
                pwr.write(3, f"{t_seq:08d}")
                pwr.write(11, f"{rec_seq:08d}")
                pwr.write(19, f"{linked['idx']:02d}") 
                pwr.write(21, f"00000000{linked['idx']}") 
                pwr.write(28, linked['orig']['name'], 45)
                pwr.write(87, linked['agreement'], 14)
                
                # GEOMETRY FIX 3: Writer Ref at 101 (Required by Parity/Manual)
                pwr.write(101, f"000000{w_idx:03d}01") 
                
                lines.append(str(pwr))
                rec_seq += 1

        # RECORDS & ORIGIN
        cd_id = row.get('ALBUM: Code', 'RC052')
        isrc = row.get('CODE: ISRC', '')
        
        rec = CwrLine("REC")
        rec.write(3, f"{t_seq:08d}")
        rec.write(11, f"{rec_seq:08d}")
        rec.write(19, now_d)
        rec.write(74, "000000")
        rec.write(154, cd_id, 14)
        rec.write(180, isrc, 12)
        rec.write(194, "CD")
        rec.write(297, "RED COLA")
        rec.write(349, "Y")
        lines.append(str(rec))
        rec_seq += 1
        
        orn = CwrLine("ORN")
        orn.write(3, f"{t_seq:08d}")
        orn.write(11, f"{rec_seq:08d}")
        orn.write(19, "LIB")
        orn.write(22, row.get('ALBUM: Title', 'UNKNOWN'), 60)
        orn.write(82, cd_id, 14)
        orn.write(96, "0001")
        orn.write(100, "RED COLA")
        lines.append(str(orn))

    lines.append(f"GRT00001{len(df):08d}{len(lines)+1:08d}")
    lines.append(f"TRL00001{len(df):08d}{len(lines)+1:08d}")
    
    return "\n".join(lines)
