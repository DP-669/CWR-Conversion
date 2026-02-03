import pandas as pd
from datetime import datetime
import re

# ==============================================================================
# CONFIGURATION
# ==============================================================================
LUMINA_CONFIG = {
    "name": "LUMINA PUBLISHING UK",
    "ipi": "01254514077",
    "territory": "0826"
}

AGREEMENT_MAP = {
    "PASHALINA": "4316161",
    "LUKACINO": "3845006",
    "TARMAC": "6781310",
    "SNOOPLE": "13990221",
    "MANNY": "13997451"
}

# ==============================================================================
# MODULE: THE ASSEMBLER (FIXED)
# ==============================================================================
class Assembler:
    def __init__(self):
        self.buffer = [' '] * 512
    def build(self, blueprint, data_dict):
        self.buffer = [' '] * 512 
        for start, length, value_template in blueprint:
            if value_template.startswith("{") and value_template.endswith("}"):
                key = value_template[1:-1]
                val = str(data_dict.get(key, ""))
            else:
                val = value_template
            val = val.strip().upper()
            val = val.ljust(length)[:length]
            for i, char in enumerate(val):
                if start + i < 512:
                    self.buffer[start + i] = char
        return "".join(self.buffer).rstrip()

# ==============================================================================
# BLUEPRINTS (Geometry)
# ==============================================================================
class Blueprints:
    HDR = [
        (0,  3,  "HDR"), (3,  11, "{sender_ipi}"), (14, 45, "{sender_name}"), 
        (59, 5,  "01.10"), (64, 8,  "{date}"), (72, 6,  "{time}"), (78, 8,  "{date}"),        
        (85, 4,  "2.20"), (98, 8,  "BACKBEAT")       
    ]
    REV = [
        (0,   3,  "REV"), (3,   8,  "{t_seq}"), (11,  8,  "00000000"),     
        (19,  60, "{title}"), (79,  2,  "  "), (81,  14, "{work_id}"),    
        (95,  11, "{iswc}"), (106, 8,  "00000000"), (114, 12, "            "),
        (126, 3,  "UNC"), (129, 6,  "{duration}"), 
        (135, 1,  "Y"), (136, 6,  "      "), (142, 3,  "ORI")           
    ]
    SPU = [
        (0,   3,  "SPU"), (3,   8,  "{t_seq}"), (11,  8,  "{rec_seq}"),
        (19,  2,  "{chain_id}"), (21,  9,  "{pub_id}"), (30,  45, "{pub_name}"),
        (76,  2,  "{role}"), (87,  11, "{ipi}"), (112, 3,  "{pr_soc}"),     
        (115, 5,  "{pr_share}"), (120, 3,  "{mr_soc}"), (123, 5,  "{mr_share}"),   
        (128, 3,  "{sr_soc}"), (131, 5,  "{sr_share}"), (137, 1,  "N"),            
        (166, 14, "{agreement}"), (180, 2,  "PG")            
    ]
    SPT = [
        (0,   3,  "SPT"), (3,   8,  "{t_seq}"), (11,  8,  "{rec_seq}"),
        (19,  9,  "{pub_id}"), (34,  5,  "{pr_share}"), (39,  5,  "{mr_share}"),
        (44,  5,  "{sr_share}"), (49,  1,  "I"), (50,  4,  "{territory}"), (55,  3,  "001")           
    ]
    SWR = [
        (0,   3,  "SWR"), (3,   8,  "{t_seq}"), (11,  8,  "{rec_seq}"),
        (19,  9,  "{writer_id}"), (28,  45, "{last_name}"), (73,  30, "{first_name}"),
        (104, 2,  "C "), (115, 11, "{ipi}"), (126, 3,  "{pr_soc}"),
        (129, 5,  "{pr_share}"), (134, 3,  "{mr_soc}"), (137, 5,  "{mr_share}"),
        (142, 3,  "{sr_soc}"), (145, 5,  "{sr_share}"), (151, 1,  "N")             
    ]
    SWT = [
        (0,   3,  "SWT"), (3,   8,  "{t_seq}"), (11,  8,  "{rec_seq}"),
        (19,  9,  "{writer_id}"), (28,  5,  "{pr_share}"), (33,  5,  "{mr_share}"),
        (38,  5,  "{sr_share}"), (43,  1,  "I"), (44,  4,  "2136"), (49,  3,  "001")
    ]
    PWR = [
        (0,   3,  "PWR"), (3,   8,  "{t_seq}"), (11,  8,  "{rec_seq}"),
        (19,  9,  "{pub_id}"), (28,  45, "{pub_name}"), (87,  14, "{agreement}"),
        (101, 11, "{writer_ref}")  
    ]
    REC = [
        (0,   3,  "REC"), (3,   8,  "{t_seq}"), (11,  8,  "{rec_seq}"), (19,  8,  "00000000"),     
        (74,  6,  "000000"), (154, 14, "{cd_id}"), (180, 12, "{isrc}"),
        (194, 2,  "{source}"), (197, 60, "{title}"), (297, 60, "{label}"), (349, 1,  "Y")
    ]
    ORN = [
        (0,   3,  "ORN"), (3,   8,  "{t_seq}"), (11,  8,  "{rec_seq}"), (19,  3,  "LIB"),
        (22,  60, "{library}"), (82,  14, "{cd_id}"), (96,  4,  "0001"), (100, 60, "{label}")
    ]

# ==============================================================================
# LOGIC ENGINE
# ==============================================================================
def pad_ipi(val):
    if not val or pd.isna(val): return "00000000000"
    clean = re.sub(r'\D', '', str(val))
    return clean.zfill(11)

def fmt_share(val):
    try:
        if pd.isna(val) or str(val).strip() == '': return "00000"
        return f"{int(round(float(val) * 100)):05d}"
    except: return "00000"

def parse_duration(val):
    if pd.isna(val) or not str(val).strip(): return "000000"
    v = str(val).strip()
    try:
        ts = int(float(v))
        m, s = divmod(ts, 60); h, m = divmod(m, 60)
        return f"{h:02d}{m:02d}{s:02d}"
    except: return "000000"

def get_vessel_col(row, base, idx, suffix):
    target = f"{base}:{idx}: {suffix}".strip().upper()
    for col in row.index:
        if target in str(col).upper():
            return row[col]
    return None

def generate_cwr_content(df):
    lines = []
    asm = Assembler()
    now = datetime.now()
    
    # 1. HDR
    lines.append(asm.build(Blueprints.HDR, {
        "sender_ipi": pad_ipi(LUMINA_CONFIG["ipi"]),
        "sender_name": LUMINA_CONFIG["name"],
        "date": now.strftime("%Y%m%d"), "time": now.strftime("%H%M%S")
    }))
    lines.append("GRHREV0000102.200000000001")

    for i, row in df.iterrows():
        t_seq = f"{i:08d}"
        
        # 2. REV (Vessel Specific Mapping)
        lines.append(asm.build(Blueprints.REV, {
            "t_seq": t_seq, 
            "title": str(row.get('TRACK: Title', 'UNKNOWN')),
            "work_id": str(row.get('TRACK: Number', i+1)), 
            "iswc": str(row.get('CODE: ISWC', '')),
            "duration": parse_duration(row.get('TRACK: Duration', '0'))
        }))

        rec_seq = 1
        pub_map = {} 
        
        # 3. PUBLISHERS (Vessel Logic)
        for p_idx in range(1, 4):
            p_name = get_vessel_col(row, "PUBLISHER", p_idx, "Name")
            if not p_name or pd.isna(p_name): continue
            
            p_name = str(p_name).strip()
            agr = "00000000"
            for k, v in AGREEMENT_MAP.items():
                if k in p_name.upper(): agr = v; break
            
            # Use Owner Performance Share from CSV
            pr_share_raw = float(get_vessel_col(row, "PUBLISHER", p_idx, "Owner Performance Share %") or 0)
            cwr_share = pr_share_raw * 0.5 # Equity Scaling
            
            # SPU: Original Publisher
            lines.append(asm.build(Blueprints.SPU, {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "chain_id": f"{p_idx:02d}",
                "pub_id": f"00000000{p_idx}", "pub_name": p_name, "role": "E ",
                "ipi": pad_ipi(get_vessel_col(row, "PUBLISHER", p_idx, "IPI")),
                "pr_soc": "021", "mr_soc": "021", "sr_soc": "   ",
                "pr_share": fmt_share(cwr_share), "mr_share": fmt_share(cwr_share), 
                "sr_share": fmt_share(cwr_share), "agreement": agr
            }))
            rec_seq += 1
            
            # SPU: Lumina (Admin)
            lum_id = "000000012"
            lines.append(asm.build(Blueprints.SPU, {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "chain_id": f"{p_idx:02d}",
                "pub_id": lum_id, "pub_name": LUMINA_CONFIG['name'], "role": "SE",
                "ipi": pad_ipi(LUMINA_CONFIG['ipi']), "pr_soc": "052",
                "pr_share": "00000", "mr_share": "00000", "sr_share": "00000", "agreement": agr
            }))
            rec_seq += 1
            
            # SPT: Vesna 100% Rule
            lines.append(asm.build(Blueprints.SPT, {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "pub_id": lum_id,
                "pr_share": fmt_share(cwr_share), "mr_share": "10000", "sr_share": "10000",
                "territory": LUMINA_CONFIG['territory']
            }))
            rec_seq += 1
            
            pub_map[p_name.upper()] = {"chain": f"{p_idx:02d}", "id": f"00000000{p_idx}", "agr": agr}

        # 4. WRITERS (Vessel Logic)
        for w_idx in range(1, 4):
            w_last = get_vessel_col(row, "WRITER", w_idx, "Last Name")
            if not w_last or pd.isna(w_last): continue
            
            # Scale share to 50% scale
            w_pr_raw = float(get_vessel_col(row, "WRITER", w_idx, "Owner Performance Share %") or 0)
            cwr_w_share = w_pr_raw * 0.5
            
            # SWR
            lines.append(asm.build(Blueprints.SWR, {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "writer_id": f"00000000{w_idx}",
                "last_name": str(w_last), "first_name": str(get_vessel_col(row, "WRITER", w_idx, "First Name") or ""),
                "ipi": pad_ipi(get_vessel_col(row, "WRITER", w_idx, "IPI")),
                "pr_soc": "021", "mr_soc": "099", "sr_soc": "099",
                "pr_share": fmt_share(cwr_w_share), "mr_share": "00000", "sr_share": "00000"
            }))
            rec_seq += 1
            
            # SWT
            lines.append(asm.build(Blueprints.SWT, {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "writer_id": f"00000000{w_idx}",
                "pr_share": fmt_share(cwr_w_share), "mr_share": "00000", "sr_share": "00000"
            }))
            rec_seq += 1
            
            # PWR
            orig_pub_name = str(get_vessel_col(row, "WRITER", w_idx, "Original Publisher") or "").strip().upper()
            if orig_pub_name in pub_map:
                p_info = pub_map[orig_pub_name]
                lines.append(asm.build(Blueprints.PWR, {
                    "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "pub_id": p_info['id'], 
                    "pub_name": orig_pub_name[:45], "agreement": p_info['agr'],
                    "writer_ref": f"0000000{w_idx}{p_info['chain']}"
                }))
                rec_seq += 1

        # 5. ARTIFACTS
        isrc_val = str(row.get('CODE: ISRC', ''))
        cd_code = str(row.get('ALBUM: Code', 'RC055'))
        lines.append(asm.build(Blueprints.REC, {
            "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "isrc": isrc_val, 
            "cd_id": cd_code, "source": "CD", "title": "", "label": "RED COLA"
        }))
        rec_seq += 1
        lines.append(asm.build(Blueprints.ORN, {
            "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "library": "RED COLA", 
            "cd_id": cd_code, "label": "RED COLA"
        }))

    lines.append(f"TRL00001{len(df):08d}{len(lines)+1:08d}")
    return "\n".join(lines)
