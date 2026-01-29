import pandas as pd
from datetime import datetime

# --- CORE CONFIGURATION ---
LUMINA_CONFIG = {
    "name": "LUMINA PUBLISHING UK",
    "ipi": "01254514077",
    "role": "SE",
    "agreement": "6781310"
}

PUBLISHER_DB = {
    "TARMAC": {"name": "TARMAC 1331 PUBLISHING", "ipi": "00356296239", "role": "E ", "agreement": "6781310"},
    "PASHALINA": {"name": "PASHALINA PUBLISHING", "ipi": "00498578867", "role": "E ", "agreement": "4316161"},
    "MANNY": {"name": "MANNY G MUSIC", "ipi": "00515125979", "role": "E ", "agreement": "13997451"}
}

def pad(val, length, is_num=False):
    if pd.isna(val): val = ""
    v = str(val).strip().upper()
    return v.zfill(length) if is_num else v.ljust(length)[:length]

def format_share(val):
    """Converts 16.5 to '01650' (CWR 5-digit format)"""
    try:
        f_val = float(val)
        return f"{int(f_val * 100):05d}"
    except:
        return "00000"

def generate_cwr_content(df):
    lines = []
    now_d, now_t = datetime.now().strftime("%Y%m%d"), datetime.now().strftime("%H%M%S")
    
    # 1. HEADER
    lines.append(f"HDR012545140LUMINA PUBLISHING UK         01.10{now_d}{now_t}{now_d}               2.2001BACKBEAT")
    lines.append("GRHREV0000102.200000000001")

    for i, row in df.iterrows():
        t_idx = i + 1
        rec_count = 1
        
        # --- WORK METADATA ---
        raw_id = row.get('CODE: ISWC') or row.get('Song_Number') or f"WORK{t_idx:07d}"
        work_id = pad(raw_id, 14)
        title = pad(row.get('TRACK: Title', 'UNKNOWN TITLE'), 60)
        isrc = pad(row.get('CODE: ISRC', ''), 12)
        library = pad(row.get('LIBRARY: Name', 'SONIC MAPS'), 60)
        cd_id = pad(row.get('ALBUM: Code', 'RC052'), 14)

        # REV record
        lines.append(f"REV{t_idx:08d}00000000{title}   {work_id}00000000UNC000025Y      ORI{' '*52}00000000000{' '*51}Y")

        # --- PUBLISHER LOOP (Original + Lumina Sub-Pub) ---
        # Note: In a production environment, we'd loop through all CSV Publisher columns.
        # Here we map the primary relationship.
        pub_name_raw = str(row.get('PUBLISHER 1: Name', 'TARMAC')).upper()
        p_orig = next((v for k, v in PUBLISHER_DB.items() if k in pub_name_raw), PUBLISHER_DB["TARMAC"])
        
        # SPU 1: Original Publisher
        p_share = format_share(row.get('PUBLISHER 1: Collection Performance Share %', 50))
        lines.append(f"SPU{t_idx:08d}{rec_count:08d}01000000000{pad(p_orig['name'], 45)}{p_orig['role']}         {pad(p_orig['ipi'], 11, True)}              0210165002103300   03300 N{' '*28}{pad(p_orig['agreement'], 14)}PG")
        rec_count += 1
        
        # SPU 2: Lumina (Sub-Publisher)
        lines.append(f"SPU{t_idx:08d}{rec_count:08d}01000000012{pad(LUMINA_CONFIG['name'], 45)}{LUMINA_CONFIG['role']}         {pad(LUMINA_CONFIG['ipi'], 11, True)}              052000000330000003300000 N{' '*28}{pad(LUMINA_CONFIG['agreement'], 14)}PG")
        rec_count += 1

        # SPT: Territory (World/UK)
        lines.append(f"SPT{t_idx:08d}{rec_count:08d}016500330003300I0826 001")
        rec_count += 1

        # --- WRITER LOOP ---
        for w_idx in range(1, 4):
            last_name = row.get(f'WRITER {w_idx}: Last Name')
            if pd.isna(last_name) or str(last_name).strip() == "": continue
            
            first_name = pad(row.get(f'WRITER {w_idx}: First Name', ''), 30)
            full_last = pad(last_name, 45)
            w_ipi = pad(row.get(f'WRITER {w_idx}: IPI', ''), 11, True)
            w_pr_share = format_share(row.get(f'WRITER {w_idx}: Collection Performance Share %', 50))
            
            # SWR Record
            lines.append(f"SWR{t_idx:08d}{rec_count:08d}000000000{full_last}{first_name} C          {w_ipi}{w_pr_share}00000990000009900000 N")
            rec_count += 1
            
            # SWT Record (Territory for Writer)
            lines.append(f"SWT{t_idx:08d}{rec_count:08d}000000000{w_pr_share}00000000000000I2136 001")
            rec_count += 1

        # --- MANDATORY ICE RECORDS ---
        lines.append(f"PWR{t_idx:08d}{rec_count:08d}01000000000{pad(p_orig['name'], 45)}{pad(p_orig['agreement'], 14)}00000000000")
        rec_count += 1
        lines.append(f"REC{t_idx:08d}{rec_count:08d}{now_d}{' '*54}000000{' '*80}{cd_id}{' '*10}{isrc}  CD{' '*103}RED COLA{' '*52}Y")
        rec_count += 1
        lines.append(f"ORN{t_idx:08d}{rec_count:08d}LIB{library}{cd_id}0254RED COLA")

    lines.append(f"GRT00001{len(df):08d}{len(lines)+1:08d}")
    lines.append(f"TRL00001{len(df):08d}{len(lines)+1:08d}")
    return "\n".join(lines)
