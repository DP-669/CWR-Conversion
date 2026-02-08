import pandas as pd
from datetime import datetime
import re

# ==============================================================================
# CONFIGURATION
# ==============================================================================
LUMINA_CONFIG = {
    "name": "LUMINA PUBLISHING UK",
    "ipi": "01254514077",
    "territory": "0826",
    "society_code": "319" # PRS Code for Filename
}

AGREEMENT_MAP = {
    "PASHALINA": "4316161",
    "LUKACINO": "3845006",
    "TARMAC": "6781310",
    "SNOOPLE": "13990221",
    "MANNY": "13997451",
    "REDCOLA": "4165777",
    "HOLLY PALMER": "13994635",
    "DEMENTIA": "13994638",
    "CULVERTOWN": "13994260",
    "VANTABLACK": "13994073",
    "TORO ROSSO": "13994607",
    "MINA": "13995081",
    "MC TROUBLE": "13996234"
}

# ==============================================================================
# MODULE: THE ASSEMBLER (GEOMETRY HARDENED)
# ==============================================================================
class Assembler:
    def __init__(self):
        self.buffer = [' '] * 512
        
    def build(self, blueprint, data_dict):
        # Clear buffer with spaces
        self.buffer = [' '] * 512 
        
        for start, length, value_template in blueprint:
            # 1. Resolve Value
            if value_template.startswith("{") and value_template.endswith("}"):
                key = value_template[1:-1]
                val = data_dict.get(key, "")
            else:
                val = value_template
            
            # 2. SANITIZE: Remove 'NAN', None, or malformed strings
            if val is None or str(val).strip().upper() == 'NAN' or str(val).strip().upper() == 'NONE':
                val = ""
            
            # 3. FORMAT: Strict Uppercase and Left-Justify with padding
            val = str(val).strip().upper()
            padded_val = val.ljust(length)[:length]
            
            # 4. INJECT: Place into specific index range
            # Note: start is 0-indexed. CWR Spec is 1-indexed.
            # Blueprints below are adjusted to 0-index.
            for i, char in enumerate(padded_val):
                if start + i < 512:
                    self.buffer[start + i] = char
                    
        return "".join(self.buffer).rstrip()

# ==============================================================================
# BLUEPRINTS (Aligned to Vesna's Feedback)
# ==============================================================================
class Blueprints:
    # HDR: Vesna Pattern: HDR + 01 + IPI + Name + Ver + Dates + 2.20 (No Backbeat)
    HDR = [
        (0,  3,  "HDR"), 
        (3,  2,  "01"),             # Vesna specific sender type
        (5,  11, "{sender_ipi}"),   # 01254514077
        (16, 45, "{sender_name}"), 
        (61, 5,  "01.10"), 
        (66, 8,  "{date}"), 
        (74, 6,  "{time}"), 
        (80, 8,  "{date}"),        
        (88, 15, "               "),# Char Set Blank
        (103, 3,  "2.2"),           # CWR Version
        (106, 2,  "00")             # Revision (Vesna showed 2.20)
    ]
    
    # GRH: Group Header
    GRH = [
        (0,  3,  "GRH"),
        (3,  3,  "NWR"),            # Transaction Type (NWR usually preferred for new)
        (6,  5,  "00001"),          # Group ID
        (11, 5,  "02.10"),          # Version
        (16, 10, "0000000000"),     # Batch ID
    ]

    # REV: "ORI" anchored at 142. Gaps enforced.
    REV = [
        (0,   3,  "REV"), 
        (3,   8,  "{t_seq}"), 
        (11,  8,  "00000000"),      
        (19,  60, "{title}"), 
        (79,  2,  "  "), 
        (81,  14, "{work_id}"),     
        (95,  11, "{iswc}"), 
        (106, 8,  "00000000"), 
        (126, 3,  "UNC"), 
        (129, 6,  "{duration}"), 
        (135, 1,  "Y"), 
        (136, 6,  "      "),        # CRITICAL GAP (Text-Music & Composite)
        (142, 3,  "ORI")            # Anchored at 142
    ]

    SPU = [
        (0,   3,  "SPU"), 
        (3,   8,  "{t_seq}"), 
        (11,  8,  "{rec_seq}"),
        (19,  2,  "{chain_id}"), 
        (21,  9,  "{pub_id}"), 
        (30,  45, "{pub_name}"),
        (76,  2,  "{role}"), 
        (78,  9,  "         "),     # Tax ID
        (87,  11, "{ipi}"), 
        (98,  14, "{agreement}"),   # Submitter Agrmt
        (112, 3,  "{pr_soc}"),      
        (115, 5,  "{pr_share}"), 
        (120, 3,  "{mr_soc}"), 
        (123, 5,  "{mr_share}"),   
        (128, 3,  "{sr_soc}"), 
        (131, 5,  "{sr_share}"), 
        (136, 1,  "N"),             
        (165, 14, "{agreement}"),   # Society Agrmt (Using same for now)
        (179, 2,  "PG")             
    ]

    SPT = [
        (0,   3,  "SPT"), 
        (3,   8,  "{t_seq}"), 
        (11,  8,  "{rec_seq}"),
        (19,  9,  "{pub_id}"), 
        (28,  6,  "      "),        # Space Gap
        (34,  5,  "{pr_share}"), 
        (39,  5,  "{mr_share}"),
        (44,  5,  "{sr_share}"), 
        (49,  1,  "I"), 
        (50,  4,  "{territory}"), 
        (55,  3,  "001")            
    ]

    SWR = [
        (0,   3,  "SWR"), 
        (3,   8,  "{t_seq}"), 
        (11,  8,  "{rec_seq}"),
        (19,  9,  "{writer_id}"), 
        (28,  45, "{last_name}"), 
        (73,  30, "{first_name}"),
        (104, 2,  "C "), 
        (115, 11, "{ipi}"),         # IPI anchored at 115
        (126, 3,  "{pr_soc}"),
        (129, 5,  "{pr_share}"), 
        (134, 3,  "{mr_soc}"), 
        (137, 5,  "{mr_share}"),
        (142, 3,  "{sr_soc}"), 
        (145, 5,  "{sr_share}"), 
        (150, 1,  "N")              
    ]

    SWT = [
        (0,   3,  "SWT"), 
        (3,   8,  "{t_seq}"), 
        (11,  8,  "{rec_seq}"),
        (19,  9,  "{writer_id}"), 
        (28,  5,  "{pr_share}"), 
        (33,  5,  "{mr_share}"),
        (38,  5,  "{sr_share}"), 
        (43,  1,  "I"), 
        (44,  4,  "2136"), 
        (49,  3,  "001")
    ]

    PWR = [
        (0,   3,  "PWR"), 
        (3,   8,  "{t_seq}"), 
        (11,  8,  "{rec_seq}"),
        (19,  9,  "{pub_id}"), 
        (28,  45, "{pub_name}"), 
        (73,  14, "{agreement}"),
        (101, 9,  "{writer_id}"),    # Writer Ref
        (110, 2,  "{chain_id}")
    ]

    REC = [
        (0,   3,  "REC"), 
        (3,   8,  "{t_seq}"), 
        (11,  8,  "{rec_seq}"), 
        (19,  8,  "00000000"),      
        (74,  6,  "{duration}"),    # Duration from REV
        (154, 14, "{cd_id}"), 
        (180, 12, "{isrc}"),
        (194, 2,  "{source}"), 
        (197, 60, "{title}"), 
        (297, 60, "{label}"), 
        (349, 1,  "Y")
    ]

    ORN = [
        (0,   3,  "ORN"), 
        (3,   8,  "{t_seq}"), 
        (11,  8,  "{rec_seq}"), 
        (19,  3,  "LIB"),
        (22,  60, "{library}"), 
        (82,  14, "{cd_id}"), 
        (96,  4,  "0001"), 
        (100, 60, "{label}")
    ]
    
    # Trailer Blueprints
    GRT = [(0, 3, "GRT"), (3, 5, "00001"), (8, 8, "{t_count}"), (16, 8, "{r_count}")]
    TRL = [(0, 3, "TRL"), (3, 5, "00001"), (8, 8, "{t_count}"), (16, 8, "{r_count}")]

# ==============================================================================
# LOGIC ENGINE
# ==============================================================================
def pad_ipi(val):
    if not val or pd.isna(val) or str(val).upper() == 'NAN': return "00000000000"
    clean = re.sub(r'\D', '', str(val))
    return clean.zfill(11)

def fmt_share(val):
    try:
        if pd.isna(val) or str(val).strip() == '' or str(val).upper() == 'NAN': return "00000"
        return f"{int(round(float(val) * 100)):05d}"
    except: return "00000"

def parse_duration(val):
    if pd.isna(val) or not str(val).strip() or str(val).upper() == 'NAN': return "000000"
    v = str(val).strip()
    try:
        if ":" in v:
            # Assume MM:SS
            parts = v.split(":")
            m = int(parts[0])
            s = int(parts[1])
            h = 0
        else:
            # Assume raw seconds
            ts = int(float(v))
            m, s = divmod(ts, 60)
            h, m = divmod(m, 60)
            
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
    
    # 1. HDR (Vesna compliant)
    lines.append(asm.build(Blueprints.HDR, {
        "sender_ipi": pad_ipi(LUMINA_CONFIG["ipi"]),
        "sender_name": LUMINA_CONFIG["name"],
        "date": now.strftime("%Y%m%d"), 
        "time": now.strftime("%H%M%S")
    }))
    
    # 2. GRH
    lines.append(asm.build(Blueprints.GRH, {}))

    transaction_count = 0
    total_record_count = 0 

    for i, row in df.iterrows():
        transaction_count += 1
        t_seq = f"{(transaction_count - 1):08d}"
        
        # Data Extraction
        title_val = str(row.get('TRACK: Title', 'UNKNOWN'))
        work_id = str(row.get('TRACK: Number', i+1))
        duration_val = parse_duration(row.get('TRACK: Duration', '0'))
        iswc_val = str(row.get('CODE: ISWC', ''))
        
        # 2. REV
        lines.append(asm.build(Blueprints.REV, {
            "t_seq": t_seq, 
            "title": title_val,
            "work_id": work_id, 
            "iswc": iswc_val,
            "duration": duration_val
        }))
        
        rec_seq = 1
        pub_map = {} 
        
        # 3. PUBLISHERS
        for p_idx in range(1, 4):
            p_name = get_vessel_col(row, "PUBLISHER", p_idx, "Name")
            if not p_name or pd.isna(p_name) or str(p_name).upper() == 'NAN': continue
            
            p_name = str(p_name).strip()
            agr = "00000000"
            for k, v in AGREEMENT_MAP.items():
                if k in p_name.upper(): agr = v; break
            
            pr_raw = get_vessel_col(row, "PUBLISHER", p_idx, "Owner Performance Share %")
            pr_share_val = float(pr_raw) if pd.notna(pr_raw) else 0.0
            
            # Logic: Input is 50/50. CWR requires 50/100/100 split for Admin.
            # Orig Pub gets 50% PR, 0% MR, 0% SR usually if Admin takes all.
            # But standard is Orig Pub 50/50/50 -> Admin 50/100/100?
            # Let's stick to simple math based on input.
            
            cwr_share = pr_share_val * 0.5 # 50 -> 25
            
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
                "ipi": pad_ipi(LUMINA_CONFIG['ipi']), "pr_soc": "052", "mr_soc": "033", "sr_soc": "033",
                "pr_share": "00000", "mr_share": "00000", "sr_share": "00000", "agreement": agr
            }))
            rec_seq += 1
            
            # SPT: Vesna Correction -> 5000 / 10000 / 10000
            lines.append(asm.build(Blueprints.SPT, {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "pub_id": lum_id,
                "pr_share": fmt_share(cwr_share), # 50% of the 50%? No, usually 5000 (50%)
                "mr_share": "10000", # Vesna Force: 100%
                "sr_share": "10000", # Vesna Force: 100%
                "territory": LUMINA_CONFIG['territory']
            }))
            rec_seq += 1
            
            pub_map[p_name.upper()] = {"chain": f"{p_idx:02d}", "id": f"00000000{p_idx}", "agr": agr}

        # 4. WRITERS
        for w_idx in range(1, 4):
            w_last = get_vessel_col(row, "WRITER", w_idx, "Last Name")
            if not w_last or pd.isna(w_last) or str(w_last).upper() == 'NAN': continue
            
            w_pr_raw = get_vessel_col(row, "WRITER", w_idx, "Owner Performance Share %")
            w_pr_val = float(w_pr_raw) if pd.notna(w_pr_raw) else 0.0
            cwr_w_share = w_pr_val * 0.5
            
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
                    "writer_id": f"00000000{w_idx}",
                    "chain_id": p_info['chain']
                }))
                rec_seq += 1

        # 5. ARTIFACTS
        isrc_val = str(row.get('CODE: ISRC', ''))
        cd_code = str(row.get('ALBUM: Code', 'RC055'))
        lines.append(asm.build(Blueprints.REC, {
            "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "isrc": isrc_val, 
            "cd_id": cd_code, "source": "CD", "title": "", "label": "RED COLA", "duration": duration_val
        }))
        rec_seq += 1
        lines.append(asm.build(Blueprints.ORN, {
            "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "library": "RED COLA", 
            "cd_id": cd_code, "label": "RED COLA"
        }))
        
        total_record_count += (rec_seq + 1) # REV + details

    # 4. TRAILERS (Calculated)
    grt_recs = total_record_count + 2 # + GRH + GRT
    trl_recs = grt_recs + 2 # + HDR + TRL
    
    lines.append(asm.build(Blueprints.GRT, {"t_count": f"{transaction_count:08d}", "r_count": f"{grt_recs:08d}"}))
    lines.append(asm.build(Blueprints.TRL, {"t_count": f"{transaction_count:08d}", "r_count": f"{trl_recs:08d}"}))
    
    return "\n".join(lines)
