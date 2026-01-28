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
    """Strict fixed-width formatting for CWR."""
    if pd.isna(val): val = ""
    v = str(val).strip().upper()
    return v.zfill(length) if is_num else v.ljust(length)[:length]

def normalize_columns(df):
    """
    Smart-Mapper: Auto-detects column names regardless of 
    spacing, capitalization, or common variations.
    """
    # 1. Clean existing headers (strip whitespace, lowercase)
    df.columns = [str(c).strip() for c in df.columns]
    
    # 2. Define known aliases for required fields
    mapping_targets = {
        'Title': ['title', 'work title', 'work_title', 'track title', 'track name', 'song name', 'song title'],
        'Song_Number': ['song_number', 'song number', 'song no', 'work id', 'work_id', 'track id', 'number', 'id'],
        'Publisher': ['publisher', 'publisher name', 'pub', 'original publisher', 'copyright', 'label'],
        'ISRC': ['isrc', 'isrc code'],
        'Library_Album': ['library_album', 'library', 'album', 'source', 'cd title', 'from album'],
        'CD_Identifier': ['cd_identifier', 'cd id', 'catalog number', 'cat no', 'catalogue number']
    }
    
    # 3. Rename columns if matches are found
    for standard, aliases in mapping_targets.items():
        # Check if we already have the standard name
        if standard in df.columns:
            continue
            
        # Look for aliases (case-insensitive)
        for col in df.columns:
            if col.lower() in aliases:
                df.rename(columns={col: standard}, inplace=True)
                break
    
    return df

def generate_cwr_content(df):
    # PRE-PROCESS: Normalize columns to ensure we find the data
    df = normalize_columns(df)
    
    lines = []
    now_d, now_t = datetime.now().strftime("%Y%m%d"), datetime.now().strftime("%H%M%S")
    
    # HEADER
    lines.append(f"HDR012545140LUMINA PUBLISHING UK         01.10{now_d}{now_t}{now_d}               2.2001BACKBEAT")
    lines.append("GRHREV0000102.200000000001")

    # TRANSACTIONS
    for i, row in df.iterrows():
        t_idx = i + 1
        
        # Publisher Lookup
        pub_raw = str(row.get('Publisher', 'TARMAC')).upper()
        p = next((v for k, v in PUBLISHER_DB.items() if k in pub_raw), PUBLISHER_DB["TARMAC"])
        
        # Data Extraction (Now robust due to normalization)
        work_id = pad(row.get('Song_Number', t_idx), 14, True)
        title = pad(row.get('Title', 'UNKNOWN TITLE'), 60)
        isrc = pad(row.get('ISRC', ''), 12)
        library = pad(row.get('Library_Album', 'SONIC MAPS'), 60)
        cd_id = pad(row.get('CD_Identifier', 'RC052'), 14)

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

    # TRAILERS
    lines.append(f"GRT00001{len(df):08d}{len(lines)+1:08d}")
    lines.append(f"TRL00001{len(df):08d}{len(lines)+1:08d}")

    return "\n".join(lines)
