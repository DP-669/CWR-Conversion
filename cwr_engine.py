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
    v = str(val).strip().upper() if not pd.isna(val) else ""
    return v.zfill(length) if is_num else v.ljust(length)[:length]

def generate_cwr_content(df):
    lines = []
    now_d, now_t = datetime.now().strftime("%Y%m%d"), datetime.now().strftime("%H%M%S")
    
    # 1. HEADER (HDR) & GROUP HEADER (GRH)
    lines.append(f"HDR012545140LUMINA PUBLISHING UK         01.10{now_d}{now_t}{now_d}               2.2001BACKBEAT")
    lines.append("GRHREV0000102.200000000001")

    # 2. TRANSACTION LOOP
    for i, row in df.iterrows():
        t_idx = i + 1
        
        # Dynamic Publisher Lookup
        pub_raw = str(row.get('Publisher', 'TARMAC')).upper()
        p = next((v for k, v in PUBLISHER_DB.items() if k in pub_raw), PUBLISHER_DB["TARMAC"])
        
        work_id = pad(row.get('Song_Number', t_idx), 14, True)
        title = pad(row.get('Title', 'UNKNOWN TITLE'), 60)
        isrc = pad(row.get('ISRC', ''), 12)
        library = pad(row.get('Library_Album', 'SONIC MAPS'), 60)
        cd_id = pad(row.get('CD_Identifier', 'RC052'), 14)

        # REV Record
        lines.append(f"REV{t_idx:08d}00000000{title}   {work_id}00000000UNC000025Y      ORI{' '*52}00000000000{' '*51}Y")

        # SPU Record
        lines.append(f"SPU{t_idx:08d}0000000101000000000{pad(p['name'], 45)}{p['role']}         {pad(p['ipi'], 11, True)}              0210165002103300   03300 N{' '*28}{pad(p['agreement'], 14)}PG")

        # SPT Record
        lines.append(f"SPT{t_idx:08d}00000002016500330003300I0826 001")

        # PWR Record (Required for Library Music)
        lines.append(f"PWR{t_idx:08d}0000000301000000000{pad(p['name'], 45)}{pad(p['agreement'], 14)}00000000000")

        # REC Record (Recording)
        lines.append(f"REC{t_idx:08d}00000004{now_d}{' '*54}000000{' '*80}{cd_id}{' '*10}{isrc}  CD{' '*103}RED COLA{' '*52}Y")

        # ORN Record (Origin)
        lines.append(f"ORN{t_idx:08d}00000005LIB{library}{cd_id}0254RED COLA")

    # 3. TRAILERS
    lines.append(f"GRT00001{len(df):08d}{len(lines)+1:08d}")
    lines.append(f"TRL00001{len(df):08d}{len(lines)+1:08d}")

    return "\n".join(lines)
