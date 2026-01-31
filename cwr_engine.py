import pandas as pd
from datetime import datetime

# ==============================================================================
# CONFIGURATION (Hardcoded Fallback for Safety)
# ==============================================================================
try:
    from mapping_config import LUMINA_CONFIG, PUBLISHER_DB
except ImportError:
    # Fallback if file missing
    LUMINA_CONFIG = {
        "name": "LUMINA PUBLISHING UK",
        "ipi": "01254514077",
        "territory": "0826"
    }
    PUBLISHER_DB = {
        # Common mappings we've seen in your files
        "TARMAC": {"name": "TARMAC 1331 PUBLISHING", "ipi": "00356296239", "agreement": "6781310"},
        "PASHALINA": {"name": "PASHALINA PUBLISHING", "ipi": "00498578867", "agreement": "4316161"},
        "MANNY": {"name": "MANNY G MUSIC", "ipi": "00515125979", "agreement": "13997451"},
        "SNOOPLE": {"name": "SNOOPLE SONGS", "ipi": "00610526488", "agreement": "13990221"}
    }

# ==============================================================================
# MODULE 1: THE BLUEPRINTS (ICE/VESNA ALIGNED)
# ==============================================================================

class Blueprints:
    # HDR: Header Record (Refined for Version 2.2 Tag)
    HDR = [
        (0,  3,  "HDR"),           
        (3,  11, "{sender_ipi}"),  
        (14, 45, "{sender_name}"), 
        (59, 5,  "01.10"),         
        (64, 8,  "{date}"),        
        (72, 6,  "{time}"),        
        (78, 8,  "{date}"),        
        (85, 4,  "2.20"),          # ICE specific version tag
        (98, 8,  "BACKBEAT")       
    ]

    # REV: Aligned to ORI (Original) type found in Bible
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
        (129, 6,  "000025"),       
        (135, 1,  "Y"),
        (136, 3,  "ORI")           # Added Work Type flag
    ]

    # SPU: Publisher Record
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

    # SPT: Territory
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

    # SWR: Writer
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

    # SWT: Writer Territory
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

    # PWR: Aligned to Bible Spacing
    PWR = [
        (0,   3,  "PWR"),
        (3,   8,  "{t_seq}"),
        (11,  8,  "{rec_seq}"),
        (19,  9,  "{pub_id}"),     
        (28,  45, "{pub_name}"),   
        (87,  14, "{agreement}"),
        (101, 11, "{writer_ref}")  
    ]

    # REC & ORN (preserves existing logic)
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

# ==============================================================================
# MODULE 2: ASSEMBLER
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
# MODULE 3: GENERATION LOGIC
# ==============================================================================

def fmt_share(val):
    try:
        if pd.isna(val) or str(val).strip() == '': return "00000"
        return f"{int(round(float(val) * 100)):05d}"
    except: return "00000"

def get_pub(raw_name):
    raw = str(raw_name).upper()
    # Simple fuzzy match
    for key, data in PUBLISHER_DB.items():
        if key in raw: return data
    # Generic Fallback
    return {"name": raw_name[:45], "ipi": "00000000000", "agreement": "00000000"}

def get_col(row, base_name, idx, suffix):
    """Smart column selector: tries 'NAME 1: Suffix' AND 'NAME:1: Suffix'"""
    # Try Format A: "WRITER 1: Last Name"
    val = row.get(f'{base_name} {idx}: {suffix}')
    if not pd.isna(val): return val
    
    # Try Format B: "WRITER:1: Last Name" (Harvest Style)
    val = row.get(f'{base_name}:{idx}: {suffix}')
    if not pd.isna(val): return val
    
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

    for i, row in df.iterrows():
        t_seq = f"{i:08d}"
        
        # ID Logic
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
        
        ctx = {
            "t_seq": t_seq,
            "title": title_val,
            "work_id": str(raw_id),
            "iswc": iswc_val,
            "cd_id": cd_id_val,
            "isrc": isrc_val,
            "library": album_title_val.upper(),
            "label": "RED COLA"
        }
        
        lines.append(asm.build(Blueprints.REV, ctx))
        
        rec_seq = 1
        pub_map = {} 
        
        # --- WRITER LOOP ---
        # We assume up to 10 writers to be safe
        writers_found = []
        
        for w_idx in range(1, 10):
            w_last = get_col(row, "WRITER", w_idx, "Last Name")
            if pd.isna(w_last): break # Stop if no more writers
            
            w_first = get_col(row, "WRITER", w_idx, "First Name")
            w_ipi = get_col(row, "WRITER", w_idx, "IPI")
            w_share_raw = get_col(row, "WRITER", w_idx, "Collection Performance Share %")
            w_orig_pub = get_col(row, "WRITER", w_idx, "Original Publisher")
            
            w_share = fmt_share(w_share_raw)
            
            writers_found.append({
                "idx": w_idx,
                "last": w_last,
                "first": w_first,
                "ipi": w_ipi,
                "share": w_share,
                "orig_pub": w_orig_pub
            })
        
        # --- PUBLISHER LOOP (Derived from Writers if explicit columns missing) ---
        # Harvest format often hides publishers inside the writer row
        unique_pubs = {}
        for w in writers_found:
            pub_name = w['orig_pub']
            if pd.isna(pub_name) or str(pub_name).strip() == '': continue
            
            if pub_name not in unique_pubs:
                unique_pubs[pub_name] = get_pub(pub_name)
        
        # Build Publisher Records (SPU/SPT)
        p_counter = 1
        for p_raw_name, p_data in unique_pubs.items():
            # Estimate share based on linked writers (simplified: 50/50 split usually)
            # For CWR generation, we often mirror the writer share for the publisher
            # This logic mimics your previous "3 Publishers" loop but makes it dynamic
            
            # SPU 1: Original
            ctx_spu = {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "chain_id": f"{p_counter:02d}",
                "pub_id": f"00000000{p_counter}", "pub_name": p_data['name'], "role": "E ",
                "ipi": p_data['ipi'], "pr_soc": "021", "pr_share": "05000", # Default 50%
                "mr_soc": "021", "mr_share": "05000", "sr_soc": "   ", "sr_share": "03300",
                "agreement": p_data['agreement']
            }
            lines.append(asm.build(Blueprints.SPU, ctx_spu))
            rec_seq += 1
            
            # SPU 2: Lumina (Administrator)
            ctx_lum = ctx_spu.copy()
            ctx_lum.update({
                "rec_seq": f"{rec_seq:08d}", "pub_id": "000000012", "pub_name": LUMINA_CONFIG['name'],
                "role": "SE", "ipi": LUMINA_CONFIG['ipi'], "pr_soc": "052", "pr_share": "00000",
                "mr_soc": "033", "mr_share": "00000", "sr_soc": "033", "sr_share": "00000" 
            })
            lines.append(asm.build(Blueprints.SPU, ctx_lum))
            rec_seq += 1
            
            # SPT
            ctx_spt = {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "pub_id": "000000012",
                "pr_share": "05000", "mr_share": "05000", "sr_share": "03300",
                "territory": LUMINA_CONFIG['territory']
            }
            lines.append(asm.build(Blueprints.SPT, ctx_spt))
            rec_seq += 1
            
            # Store ID for linking
            unique_pubs[p_raw_name]['internal_id'] = f"00000000{p_counter}"
            unique_pubs[p_raw_name]['chain_idx'] = p_counter
            p_counter += 1

        # Build Writer Records (SWR/SWT/PWR)
        for w in writers_found:
            ctx_swr = {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", 
                "writer_id": f"00000000{w['idx']}",
                "last_name": w['last'], 
                "first_name": w.get('first', ''),
                "ipi": w.get('ipi', ''), 
                "pr_soc": "021", "pr_share": w['share'],
                "mr_soc": "099", "mr_share": "00000", "sr_soc": "099", "sr_share": "00000"
            }
            lines.append(asm.build(Blueprints.SWR, ctx_swr))
            rec_seq += 1
            
            ctx_swt = {
                "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "writer_id": f"00000000{w['idx']}",
                "pr_share": w['share'], "mr_share": "00000", "sr_share": "00000"
            }
            lines.append(asm.build(Blueprints.SWT, ctx_swt))
            rec_seq += 1
            
            # PWR Link
            orig_pub_name = w['orig_pub']
            if orig_pub_name in unique_pubs:
                p_info = unique_pubs[orig_pub_name]
                ctx_pwr = {
                    "t_seq": t_seq, "rec_seq": f"{rec_seq:08d}",
                    "pub_id": p_info['internal_id'], 
                    "pub_name": p_info['name'],
                    "agreement": p_info['agreement'], 
                    "writer_ref": f"000000{w['idx']:03d}{p_info['chain_idx']:02d}"
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
