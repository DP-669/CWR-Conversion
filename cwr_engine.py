import pandas as pd
from datetime import datetime

# Import Configuration with Fallback
try:
    from mapping_config import LUMINA_CONFIG, PUBLISHER_DB
except ImportError:
    LUMINA_CONFIG = {"name": "ERROR", "ipi": "00000000000", "territory": "0000"}
    PUBLISHER_DB = {}

# ==============================================================================
# MODULE 1: THE BLUEPRINTS (GEOMETRY LAYER)
# ==============================================================================

class Blueprints:
    # HDR: Header Record (Aligned to ICE)
    HDR = [
        (0,  3,  "HDR"),           
        (3,  11, "{sender_ipi}"),  
        (14, 45, "{sender_name}"), 
        (59, 5,  "01.10"),         
        (64, 8,  "{date}"),        
        (72, 6,  "{time}"),        
        (78, 8,  "{date}"),        
        (98, 8,  "BACKBEAT")       
    ]

    # REV: Work Registration Record
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
        (135, 1,  "Y")             
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

    # SPT: Publisher Territory Record
    SPT = [
        (0,   3,  "SPT"),
        (3,   8,  "{t_seq}"),
        (11,  8,  "{rec_seq}"),
        (19,  9,  "{pub_id}"),     
        (28,  6,  "      "),       
        (34,  5,  "{pr_share}"),
        (39,  5,  "{mr_share}"),
        (44,  5,  "{sr_share}"),
        (49,  1,  "I"),            
        (50,  4,  "{territory}"),  
        (55,  3,  "001")           
    ]

    # SWR: Writer Record
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

    # SWT: Writer Territory Record
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

    # PWR: Publisher-Writer Link Record
    # [FIXED]: Removed Chain ID to match ICE Bible format
    PWR = [
        (0,   3,  "PWR"),
        (3,   8,  "{t_seq}"),
        (11,  8,  "{rec_seq}"),
        (19,  9,  "{pub_id}"),     # Starts at 19
        (28,  45, "{pub_name}"),   # Starts at 28
        (87,  14, "{agreement}"),
        (101, 11, "{writer_ref}")  
    ]

    # REC: Recording Record
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

    # ORN: Origin Record
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
# MODULE 2: THE ASSEMBLER (EXECUTION LAYER)
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
# MODULE 3: THE DATA LOGIC (BUSINESS LAYER)
# ==============================================================================

def fmt_share(val):
    try:
        if pd.isna(val) or str(val).strip() == '': return "00000"
        return f"{int(round(float(val) * 100)):05d}"
    except: return "00000"

def get_pub(raw_name):
    raw = str(raw_name).upper()
    for key, data in PUBLISHER_DB.items():
        if key in raw: return data
    return {"name": raw_name[:45], "ipi": "00000000000", "agreement": "00000000"}

def generate_cwr_content(df):
    lines = []
    asm = Assembler()
    
    # Global Data
    now = datetime.now()
    global_ctx = {
        "date": now.strftime("%Y%m%d"),
        "time": now.strftime("%H%M%S"),
        "sender_ipi": LUMINA_CONFIG["ipi"],
        "sender_name": LUMINA_CONFIG["name"]
    }
    
    # 1. HEADER
    lines.append(asm.build(Blueprints.HDR, global_ctx))
    lines.append("GRHREV0000102.200000000001")

    # 2. TRANSACTIONS
    for i, row in df.iterrows():
        t_seq = f"{i:08d}"
        
        # ID Logic
        raw_id = row.get('Song_Number')
        if pd.isna(raw_id): raw_id = row.get('CODE: Song Code')
        if pd.isna(raw_id): 
            track_num = int(row.get('TRACK: Number', 0))
            raw_id = f"{track_num:07d}"
        
        submitter_id = str(raw_id)
        title_val = str(row.get('TRACK: Title', 'UNKNOWN TITLE'))
        iswc_val = str(row.get('CODE: ISWC', ''))
        isrc_val = str(row.get('CODE: ISRC', ''))
        cd_id_val = str(row.get('ALBUM: Code', 'RC052'))
        album_title_val = str(row.get('ALBUM: Title', 'UNKNOWN'))
        
        ctx = {
            "t_seq": t_seq,
            "title": title_val,
            "work_id": submitter_id,
            "iswc": iswc_val,
            "cd_id": cd_id_val,
            "isrc": isrc_val,
            "library": album_title_val.upper(),
            "label": "RED COLA"
        }
        
        # REV
        lines.append(asm.build(Blueprints.REV, ctx))
        
        rec_seq = 1
        pub_map = {} 

        # --- PUBLISHERS ---
        for p_idx in range(1, 4):
            p_name = row.get(f'PUBLISHER {p_idx}: Name')
            if pd.isna(p_name): continue
            
            p_data = get_pub(p_name)
            p_shares = {
                "pr": fmt_share(row.get(f'PUBLISHER {p_idx}: Collection Performance Share %')),
                "mr": fmt_share(row.get(f'PUBLISHER {p_idx}: Collection Mechanical Share %'))
            }
            
            # SPU 1: Original
            ctx_spu = {
                "t_seq": t_seq,
                "rec_seq": f"{rec_seq:08d}",
                "chain_id": f"{p_idx:02d}",
                "pub_id": f"00000000{p_idx}",
                "pub_name": p_data['name'],
                "role": "E ",
                "ipi": p_data['ipi'],
                "pr_soc": "021", "pr_share": p_shares['pr'],
                "mr_soc": "021", "mr_share": p_shares['mr'],
                "sr_soc": "   ", "sr_share": "03300",
                "agreement": p_data['agreement']
            }
            lines.append(asm.build(Blueprints.SPU, ctx_spu))
            rec_seq += 1
            
            # SPU 2: Lumina
            ctx_lum = ctx_spu.copy()
            ctx_lum.update({
                "rec_seq": f"{rec_seq:08d}",
                "pub_id": "000000012",
                "pub_name": LUMINA_CONFIG['name'],
                "role": "SE",
                "ipi": LUMINA_CONFIG['ipi'],
                "pr_soc": "052", "pr_share": "00000",
                "mr_soc": "033", "mr_share": "00000",
                "sr_soc": "033", "sr_share": "00000" 
            })
            lines.append(asm.build(Blueprints.SPU, ctx_lum))
            rec_seq += 1
            
            # SPT
            ctx_spt = {
                "t_seq": t_seq,
                "rec_seq": f"{rec_seq:08d}",
                "pub_id": "000000012",
                "pr_share": p_shares['pr'],
                "mr_share": p_shares['mr'],
                "sr_share": "03300",
                "territory": LUMINA_CONFIG['territory']
            }
            lines.append(asm.build(Blueprints.SPT, ctx_spt))
            rec_seq += 1
            
            pub_map[p_data['name']] = {"idx": p_idx, "agreement": p_data['agreement'], "orig": p_data}

        # --- WRITERS ---
        for w_idx in range(1, 4):
            w_last = row.get(f'WRITER {w_idx}: Last Name')
            if pd.isna(w_last): continue
            
            w_shares = fmt_share(row.get(f'WRITER {w_idx}: Collection Performance Share %'))
            
            ctx_swr = {
                "t_seq": t_seq,
                "rec_seq": f"{rec_seq:08d}",
                "writer_id": f"00000000{w_idx}",
                "last_name": w_last,
                "first_name": row.get(f'WRITER {w_idx}: First Name', ''),
                "ipi": row.get(f'WRITER {w_idx}: IPI', ''),
                "pr_soc": "021", "pr_share": w_shares,
                "mr_soc": "099", "mr_share": "00000",
                "sr_soc": "099", "sr_share": "00000"
            }
            lines.append(asm.build(Blueprints.SWR, ctx_swr))
            rec_seq += 1
            
            # SWT
            ctx_swt = {
                "t_seq": t_seq,
                "rec_seq": f"{rec_seq:08d}",
                "writer_id": f"00000000{w_idx}",
                "pr_share": w_shares,
                "mr_share": "00000",
                "sr_share": "00000"
            }
            lines.append(asm.build(Blueprints.SWT, ctx_swt))
            rec_seq += 1
            
            # PWR
            orig_pub = str(row.get(f'WRITER {w_idx}: Original Publisher')).upper()
            linked = next((v for k, v in pub_map.items() if k in orig_pub), None)
            
            if linked:
                # [FIXED] PWR now uses simplified context (No chain_id)
                ctx_pwr = {
                    "t_seq": t_seq,
                    "rec_seq": f"{rec_seq:08d}",
                    # "chain_id": "00", # REMOVED to match ICE
                    "pub_id": f"00000000{linked['idx']}",
                    "pub_name": linked['orig']['name'],
                    "agreement": linked['agreement'],
                    "writer_ref": f"000000{w_idx:03d}{linked['idx']:02d}"
                }
                lines.append(asm.build(Blueprints.PWR, ctx_pwr))
                rec_seq += 1

        # --- ARTIFACTS ---
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

    # TRAILERS
    count_df = len(df)
    count_lines = len(lines) + 2
    
    lines.append(f"GRT00001{count_df:08d}{count_lines:08d}")
    lines.append(f"TRL00001{count_df:08d}{count_lines:08d}")
    
    return "\n".join(lines)
