import pandas as pd
from datetime import datetime
import re

# ==============================================================================
# CONFIGURATION: THE "VESNA RULES"
# ==============================================================================

FIXED_PUB_IDS = {
    "TARMAC": "000000001",
    "PASHALINA": "000000006",
    "LUKACINO": "000000008",
    "SNOOPLE": "000000009",
    "LUMINA": "000000012",
    "MANNY": "000000013"
}

FIXED_WRITER_IDS = {
    "WHEELER": "000000001",
    "PRICE": "000000002",
    "FAZIO": "000000028"
}

AGREEMENT_MAP = {
    "TARMAC": "6781310",
    "PASHALINA": "4316161",
    "LUKACINO": "3845006",
    "SNOOPLE": "13990221",
    "MANNY": "13997451"
}

try:
    from mapping_config import LUMINA_CONFIG
except ImportError:
    LUMINA_CONFIG = {"name": "LUMINA PUBLISHING UK", "ipi": "01254514077", "territory": "0826"}

# ==============================================================================
# BLUEPRINTS (Geometry)
# ==============================================================================

class Blueprints:
    HDR = [
        (0,  3,  "HDR"),           
        (3,  11, "{sender_ipi}"),  
        (14, 45, "{sender_name}"), 
        (59, 5,  "01.10"),         
        (64, 8,  "{date}"),        
        (72, 6,  "{time}"),        
        (78, 8,  "{date}"),        
        (85, 4,  "2.20"),          
        (98, 8,  "BACKBEAT")       
    ]

    REV = [
        (0,   3,  "REV"),
        (3,   8,  "{t_seq}"),      
        (11,  8,  "00000000"),     
        (19,  60, "{title}"),      
        (79,  2,  "  "),           
        (81,  14, "{work_id}"),    
        (95,  11, "{iswc}"),       
        (106, 8,  "00000000"),     
        (126, 3,  "{duration}"),   # DYNAMIC
        (129, 6,  "000025"),       # Fallback / Padding if needed (Overwritten by duration logic usually)
        (135, 1,  "Y"),            
        (136, 6,  "      "),       # The "Vesna Gap"
        (142, 3,  "ORI")           # Work Type
    ]

    # Adjusted REV blueprint to ensure duration sits at 126 and overwrites defaults
    REV_DYNAMIC = [
        (0,   3,  "REV"),
        (3,   8,  "{t_seq}"),      
        (11,  8,  "00000000"),     
        (19,  60, "{title}"),      
        (79,  2,  "  "),           
        (81,  14, "{work_id}"),    
        (95,  11, "{iswc}"),       
        (106, 8,  "00000000"),     
        (114, 12, "            "), # Empty Space
        (126, 3,  "UNC"),          # Duration Type
        (129, 6,  "{duration}"),   # HHMMSS
        (135, 1,  "Y"),            
        (136, 6,  "      "),       
        (142, 3,  "ORI")           
    ]

    SPU = [
        (0,   3,  "SPU"),
        (3,   8,  "{t_seq}"),
        (11,  8,  "{rec_seq}"),
        (19,  2,  "{chain_id}"),
        (21,  9,  "{pub_id}"),
        (30,  45, "{pub_name}"),
        (76,  2,  "{role}"),       
        (87,  11, "{ipi}"),        
        (112, 3,  "{pr_soc}"),     
        (115, 5,  "{pr_share}"),   
        (120, 3,  "{mr_soc}"),     
        (123, 5,  "{mr_share}"),   
        (128, 3,  "{sr_soc}"),     
        (131, 5,  "{sr_share}"),   
        (137, 1,  "N"),            
        (166, 14, "{agreement}"),  
        (180, 2,  "PG")            
    ]

    SPT = [
        (0,   3,  "SPT"),
        (3,   8,  "{t_seq}"),
        (11,  8,  "{rec_seq}"),
        (19,  9,  "{pub_id}"),     
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
        (115, 11, "{ipi}"),
        (126, 3,  "{pr_soc}"),
        (129, 5,  "{pr_share}"),
        (134, 3,  "{mr_soc}"),
        (137, 5,  "{mr_share}"),
        (142, 3,  "{sr_soc}"),
        (145, 5,  "{sr_share}"),
        (151, 1,  "N")             
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
        (87,  14, "{agreement}"),
        (101, 11, "{writer_ref}")  
    ]

    REC = [
        (0,   3,  "REC"),
        (3,   8,  "{t_seq}"),
        (11,  8,  "{rec_seq}"),
        (19,  8,  "00000000"),     
        (74,  6,  "000000"),       
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
# LOGIC ENGINE
# ==============================================================================

def fmt_share(val):
    try:
        if pd.isna(val) or str(val).strip() == '': return "00000"
        return f"{int(round(float(val) * 100)):05d}"
    except: return "00000"

def parse_duration(val):
    """Converts '2:35' or '155' (seconds) to '000235' (HHMMSS)"""
    if pd.isna(val) or str(val).strip() == '':
        return "000000"
    
    val_str = str(val).strip()
    
    # Check if colons exist (MM:SS)
    if ':' in val_str:
        parts = val_str.split(':')
        if len(parts) == 2: # MM:SS
            m, s = int(parts[0]), int(parts[1])
            h = 0
        elif len(parts) == 3: # HH:MM:SS
            h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        else:
            return "000000"
    else:
        # Assume Seconds
        try:
            total_seconds = int(float(val_str))
            h = total_seconds // 3600
            m = (total_seconds % 3600) // 60
            s = total_seconds % 60
        except:
            return "000000"

    return f"{h:02d}{m:02d}{s:02d}"

def get_col(row, base_name, idx, suffix):
    val = row.get(f'{base_name} {idx}: {suffix}')
    if not pd.isna(val): return val
    val = row.get(f'{base_name}:{idx}: {suffix}')
    if not pd.isna(val): return val
    return None

def lookup_id(name, type_dict):
    upper_name = str(name).upper()
    for key, fixed_id in type_dict.items():
        if key in upper_name:
            return fixed_id
    return None

def generate_cwr_content(df):
    lines = []
    asm = Assembler()
    now = datetime.now()
    global_ctx = {
        "date": now.strftime("%Y%m%d"),
        "time": now.strftime("%H%M%S"),
        "sender_ipi": LUMINA_CONFIG["ipi"],
        "sender_name": LUMINA_CONFIG["name"]
    }
    
    lines.append(asm.build(Blueprints.HDR, global_ctx))
    lines.append("GRHREV0000102.200000000001")

    unknown_pub_counter = 90
    unknown_writer_counter = 90
    
    for i, row in df.iterrows():
        t_seq = f"{i:08d}"
        
        # --- REV DATA ---
        raw_id = row.get('Song_Number')
        if pd.isna(raw_id): raw_id = row.get('CODE: Song Code')
        if pd.isna(raw_id): 
            track_num = int(row.get('TRACK: Number', 0))
            raw_id = f"{track_num:07d}"
            
        title_val = str(row.get('TRACK: Title', 'UNKNOWN TITLE'))
        iswc_val = str(row.get('CODE: ISWC', ''))
        isrc_val = str(row.get('CODE: ISRC', ''))
        cd_id_val = str(row.get('ALBUM: Code', 'RC055'))
        album_title_val = str(row.get('ALBUM: Title', 'ALBUM'))
        
        # DYNAMIC DURATION
        dur_raw = row.get('TRACK: Duration', '0')
        dur_cwr = parse_duration(dur_raw)
        
        ctx = {
            "t_seq": t_seq, "title": title_val, "work_id": str(raw_id),
            "iswc": iswc_val, "cd_id": cd_id_val, "isrc": isrc_val,
            "library": album_title_val.upper(), "label": "RED COLA",
            "duration": dur_cwr
        }
        lines.append(asm.build(Blueprints.REV_DYNAMIC, ctx))
        rec_seq = 1
        
        # --- WRITERS (Extract Shares) ---
        writers_found = []
        total_writer_pr = 0.0
        total_writer_mr = 0.0
        total_writer_sr = 0.0
        
        for w_idx in range(1, 10):
            w_last = get_col(row, "WRITER", w_idx, "Last Name")
            if pd.isna(w_last): break 
            
            w_first = get_col(row, "WRITER", w_idx, "First Name")
            w_ipi = get_col(row, "WRITER", w_idx, "IPI")
            
            # Raw Shares (Float for calculation)
            pr_raw = get_col(row, "WRITER", w_idx, "Collection Performance Share %")
            mr_raw = get_col(row, "WRITER", w_idx, "Collection Mechanical Share %")
            # Default to 0 if missing (Common in libraries)
            pr_float = float(pr_raw) if pd.notna(pr_raw) else 0.0
            mr_float = float(mr_raw) if pd.notna(mr_raw) else 0.0
            # Sync often mirrors Mech
            sr_float = mr_float 
            
            total_writer_pr += pr_float
            total_writer_mr += mr_float
            total_writer_sr += sr_float
            
            w_orig_pub = get_col(row, "WRITER", w_idx, "Original Publisher")
            
            w_id = lookup_id(w_last, FIXED_WRITER_IDS)
            if not w_id:
                w_id = f"0000000{unknown_writer_counter}"
                unknown_writer_counter += 1
                
            writers_found.append({
                "id": w_id, "last": w_last, "first": w_first,
                "ipi": w_ipi, 
                "pr_share_fmt": fmt_share(pr_float),
                "mr_share_fmt": fmt_share(mr_float),
                "sr_share_fmt": fmt_share(sr_float),
                "orig_pub": w_orig_pub
            })
            
        # --- PUBLISHER BALANCE LOGIC ---
        # Calculate what remains for the publisher (100 - Writer Total)
        # We assume one main publisher group (or split equally if multiple).
        # For this specific workflow, we link writers to their original pub.
        
        # Default remainder
        rem_pr = max(0, 100.0 - total_writer_pr)
        rem_mr = max(0, 100.0 - total_writer_mr)
        rem_sr = max(0, 100.0 - total_writer_sr)

        unique_pubs = {}
        pub_count = 0
        
        # Identify Publishers
        for w in writers_found:
            p_name = w['orig_pub']
            if pd.isna(p_name) or str(p_name).strip() == '': continue
            if p_name not in unique_pubs:
                pub_count += 1
                unique_pubs[p_name] = {"name": p_name}
        
        # Assign Shares to Publishers (Split remainder equally)
        if pub_count > 0:
            share_per_pub_pr = rem_pr / pub_count
            share_per_pub_mr = rem_mr / pub_count
            share_per_pub_sr = rem_sr / pub_count
        else:
            share_per_pub_pr = 0
            share_per_pub_mr = 0
            share_per_pub_sr = 0

        # Populate Publisher Data
        for p_name in unique_pubs:
            p_id = lookup_id(p_name, FIXED_PUB_IDS)
            if not p_id:
                p_id = f"0000000{unknown_pub_counter}"
                unknown_pub_counter += 1
            
            agr = "00000000"
            for k, v in AGREEMENT_MAP.items():
                if k in str(p_name).upper(): agr = v; break
            
            unique_pubs[p_name].update({
                "id": p_id, "agreement": agr, "ipi": "00000000000",
                "pr_fmt": fmt_share(share_per_pub_pr),
                "mr_fmt": fmt_share(share_per_pub_mr),
                "sr_fmt": fmt_share(share_per_pub_sr)
            })

        # --- BUILD RECORDS ---
        p_chain_idx = 1
        for p_raw, p_data in unique_pubs.items():
            # SPU 1: Original Publisher (Ownership)
            ctx_spu = {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "chain_id": f"{p_chain_idx:02d}",
                "pub_id": p_data['id'], "pub_name": p_data['name'], "role": "E ",
                "ipi": p_data['ipi'], "pr_soc": "021", 
                "pr_share": p_data['pr_fmt'], # DYNAMIC
                "mr_soc": "021", 
                "mr_share": p_data['mr_fmt'], # DYNAMIC
                "sr_soc": "   ", 
                "sr_share": p_data['sr_fmt'], # DYNAMIC
                "agreement": p_data['agreement']
            }
            lines.append(asm.build(Blueprints.SPU, ctx_spu))
            rec_seq += 1
            
            # SPU 2: Lumina (Administrator)
            lum_id = FIXED_PUB_IDS["LUMINA"]
            ctx_lum = ctx_spu.copy()
            ctx_lum.update({
                "rec_seq": f"{rec_seq:08d}", "pub_id": lum_id, "pub_name": LUMINA_CONFIG['name'],
                "role": "SE", "ipi": LUMINA_CONFIG['ipi'], "pr_soc": "052", 
                "pr_share": "00000", "mr_share": "00000", "sr_share": "00000" 
            })
            lines.append(asm.build(Blueprints.SPU, ctx_lum))
            rec_seq += 1
            
            # SPT (Territory) - ADMINISTRATOR COLLECTION RULE
            # PR: Matches the Original Pub's PR share (Standard Admin Deal)
            # MR/SR: 100% (The Admin collects all mechanicals in their territory)
            ctx_spt = {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "pub_id": lum_id,
                "pr_share": p_data['pr_fmt'], 
                "mr_share": "10000", # FORCE 100%
                "sr_share": "10000", # FORCE 100%
                "territory": LUMINA_CONFIG['territory']
            }
            lines.append(asm.build(Blueprints.SPT, ctx_spt))
            rec_seq += 1
            
            unique_pubs[p_raw]['chain_idx'] = p_chain_idx
            p_chain_idx += 1

        for w in writers_found:
            ctx_swr = {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "writer_id": w['id'],
                "last_name": w['last'], "first_name": w.get('first', ''),
                "ipi": w.get('ipi', ''), "pr_soc": "021", "pr_share": w['pr_share_fmt'],
                "mr_soc": "099", "mr_share": w['mr_share_fmt'], 
                "sr_soc": "099", "sr_share": w['sr_share_fmt']
            }
            lines.append(asm.build(Blueprints.SWR, ctx_swr))
            rec_seq += 1
            
            ctx_swt = {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "writer_id": w['id'],
                "pr_share": w['pr_share_fmt'], "mr_share": w['mr_share_fmt'], "sr_share": w['sr_share_fmt']
            }
            lines.append(asm.build(Blueprints.SWT, ctx_swt))
            rec_seq += 1
            
            orig_pub = w['orig_pub']
            if orig_pub in unique_pubs:
                p_data = unique_pubs[orig_pub]
                ctx_pwr = {
                    "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}",
                    "pub_id": p_data['id'], "pub_name": p_data['name'],
                    "agreement": p_data['agreement'], 
                    "writer_ref": f"000000{int(w['id']):03d}{p_data['chain_idx']:02d}"
                }
                lines.append(asm.build(Blueprints.PWR, ctx_pwr))
                rec_seq += 1

        # ARTIFACTS
        ctx_rec_cd = {
            "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}",
            "cd_id": cd_id_val, "isrc": isrc_val, "source": "CD", "title": "", "label": "RED COLA"
        }
        lines.append(asm.build(Blueprints.REC, ctx_rec_cd))
        rec_seq += 1
        
        ctx_rec_dw = {
            "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}",
            "cd_id": "", "isrc": isrc_val, "source": "DW", "title": title_val, "label": ""
        }
        lines.append(asm.build(Blueprints.REC, ctx_rec_dw))
        rec_seq += 1
        
        ctx_orn = {
            "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}",
            "library": album_title_val.upper(), "cd_id": cd_id_val, "label": "RED COLA"
        }
        lines.append(asm.build(Blueprints.ORN, ctx_orn))

    count_df = len(df)
    count_lines = len(lines) + 2
    lines.append(f"GRT00001{count_df:08d}{count_lines:08d}")
    lines.append(f"TRL00001{count_df:08d}{count_lines:08d}")
    
    return "\n".join(lines)
