import pandas as pd
from datetime import datetime

# --- ICE VALIDATED PUBLISHER & AGREEMENT DATABASE ---
PUBLISHER_DB = {
    "TARMAC": {"name": "TARMAC 1331 PUBLISHING", "ipi": "00356296239", "role": "E ", "agreement": "6781310"},
    "LUMINA": {"name": "LUMINA PUBLISHING UK", "ipi": "01254514077", "role": "SE", "agreement": "6781310"},
    "PASHALINA": {"name": "PASHALINA PUBLISHING", "ipi": "00498578867", "role": "E ", "agreement": "4316161"},
    "MANNY": {"name": "MANNY G MUSIC", "ipi": "00515125979", "role": "E ", "agreement": "13997451"}
}

def pad(val, length, is_num=False):
    """Strict fixed-width formatting."""
    if pd.isna(val): val = ""
    v = str(val).strip().upper()
    return v.zfill(length) if is_num else v.ljust(length)[:length]

def generate_cwr_content(df):
    lines = []
    now_d, now_t = datetime.now().strftime("%Y%m%d"), datetime.now().strftime("%H%M%S")
    
    # 1. HEADER (HDR)
    lines.append(f"HDR012545140LUMINA PUBLISHING UK         01.10{now_d}{now_t}{now_d}               2.2001BACKBEAT")
    lines.append("GRHREV0000102.200000000001")

    # 2. TRANSACTION LOOP
    for i, row in df.iterrows():
        t_idx = i + 1
        
        # --- LOGIC FIX 1: DYNAMIC PUBLISHER ---
        # Look for "Publisher" column. Fallback to TARMAC if missing/empty.
        pub_raw = str(row.get('Publisher', 'TARMAC')).upper()
        # Find the correct DB entry based on the row value
        p = next((v for k, v in PUBLISHER_DB.items() if k in pub_raw), PUBLISHER_DB["TARMAC"])
        
        # --- LOGIC FIX 2: ID PRESERVATION ---
        # Look for "Song_Number" or "Work ID". If missing, use loop index.
        # This fixes the "0000001" bug.
        raw_id = row.get('Song_Number') if 'Song_Number' in df.columns else row.get('Work ID', t_idx)
        work_id = pad(raw_id, 14, True)
        
        # Look for "Title". Fallback to UNKNOWN only if completely missing.
        raw_title = row.get('Title') if 'Title' in df.columns else row.get('Work Title', 'UNKNOWN TITLE')
        title = pad(raw_title, 60)
        
        # Library Metadata (Needed for ICE)
        library = pad(row.get('Library_Album', 'SONIC MAPS'), 60)
        cd_id = pad(row.get('CD_Identifier', 'RC052'), 14)
        isrc = pad(row.get('ISRC', ''), 12)

        # REV (Work)
        lines.append(f"REV{t_idx:08d}00000000{title}   {work_id}00000000UNC000025Y      ORI{' '*52}00000000000{' '*51}Y")

        # SPU (Publisher)
        lines.append(f"SPU{t_idx:08d}0000000101000000000{pad(p['name'], 45)}{p['role']}         {pad(p['ipi'], 11, True)}              0210165002103300   03300 N{' '*28}{pad(p['agreement'], 14)}PG")

        # SPT (Territory)
        lines.append(f"SPT{t_idx:08d}00000002016500330003300I0826 001")

        # PWR (Publisher for Recording)
        lines.append(f"PWR{t_idx:08d}0000000301000000000{pad(p['name'], 45)}{pad(p['agreement'], 14)}00000000000")

        # REC (Recording)
        lines.append(f"REC{t_idx:08d}00000004{now_d}{' '*54}000000{' '*80}{cd_id}{' '*10}{isrc}  CD{' '*103}RED COLA{' '*52}Y")

        # ORN (Origin)
        lines.append(f"ORN{t_idx:08d}00000005LIB{library}{cd_id}0254RED COLA")

    # 3. TRAILERS
    lines.append(f"GRT00001{len(df):08d}{len(lines)+1:08d}")
    lines.append(f"TRL00001{len(df):08d}{len(lines)+1:08d}")

    return "\n".join(lines)
