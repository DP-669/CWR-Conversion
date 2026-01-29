import pandas as pd
from datetime import datetime
import math

# --- CONFIGURATION ---
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

def pad(val, length, is_num=False):
    """Strict CWR Padding."""
    if pd.isna(val): val = ""
    val = str(val).strip().upper()
    if is_num and val.endswith('.0'): val = val[:-2]
    return val.zfill(length) if is_num else val.ljust(length)[:length]

def format_share(val):
    """Converts 16.5 -> 01650."""
    try:
        if pd.isna(val) or str(val).strip() == '': return "00000"
        return f"{int(round(float(val) * 100)):05d}"
    except: return "00000"

def get_pub_data(raw_name):
    raw = str(raw_name).upper()
    for key, data in PUBLISHER_DB.items():
        if key in raw: return data
    return {"name": pad(raw_name, 45), "ipi": "00000000000", "agreement": "00000000"}

def generate_cwr_content(df):
    lines = []
    now_d, now_t = datetime.now().strftime("%Y%m%d"), datetime.now().strftime("%H%M%S")
    
    # HEADER (Matches London format)
    lines.append(f"HDR{pad(LUMINA_CONFIG['ipi'], 11)}LUMINA PUBLISHING UK                         01.10{now_d}{now_t}{now_d}               2.2001BACKBEAT")
    lines.append("GRHREV0000102.200000000001")

    for i, row in df.iterrows():
        # London files start transaction counts at 00000000 for the REV line
        t_seq = i 
        
        # --- METADATA ---
        # Logic: Use ISWC first, then Song Number, then Track Number
        raw_id = row.get('CODE: ISWC')
        if pd.isna(raw_id): raw_id = row.get('Song_Number')
        if pd.isna(raw_id): raw_id = str(row.get('TRACK: Number', '0')).zfill(7)
        
        # London Parity uses '0003606' style IDs in the Work ID field (Pos 60)
        # We map your CSV 'Song_Number' or 'Track Number' here.
        submitter_id = pad(raw_id, 14)
        
        title = pad(row.get('TRACK: Title', 'UNKNOWN TITLE'), 60)
        iswc = pad(row.get('CODE: ISWC', ''), 11)
        if not iswc.startswith('T'): iswc = '           '

        # REV RECORD (Fixed 12-space gap before UNC)
        lines.append(f"REV{t_seq:08d}00000000{title}   {submitter_id}{iswc}00000000            UNC000025Y      ORI{' '*52}00000000000{' '*51}Y")

        rec_seq = 1
        pub_map = {} # To link Writers to Publishers later

        # --- PUBLISHERS ---
        for p_idx in range(1, 4):
            p_name = row.get(f'PUBLISHER {p_idx}: Name')
            if pd.isna(p_name): continue
            
            p_data = get_pub_data(p_name)
            p_share_pr = format_share(row.get(f'PUBLISHER {p_idx}: Collection Performance Share %'))
            p_share_mr = format_share(row.get(f'PUBLISHER {p_idx}: Collection Mechanical Share %'))
            
            # SPU 1: Original
            lines.append(f"SPU{t_seq:08d}{rec_seq:08d}0{p_idx}00000000{p_idx}{pad(p_data['name'], 45)}E          {pad(p_data['ipi'], 11, True)}              021{p_share_pr}021{p_share_mr}   {format_share(33)} N{' '*28}{pad(p_data['agreement'], 14)}PG")
            rec_seq += 1
            
            # SPU 2: Lumina
            lines.append(f"SPU{t_seq:08d}{rec_seq:08d}0{p_idx}000000012{pad(LUMINA_CONFIG['name'], 45)}{LUMINA_CONFIG['role']}         {pad(LUMINA_CONFIG['ipi'], 11, True)}              052000000330000003300000 N{' '*28}{pad(p_data['agreement'], 14)}PG")
            rec_seq += 1
            
            # SPT: Territory
            lines.append(f"SPT{t_seq:08d}{rec_seq:08d}{p_share_pr}{p_share_mr}{format_share(33)}I{LUMINA_CONFIG['territory']} 001")
            rec_seq += 1
            
            pub_map[p_data['name']] = {"chain": f"0{p_idx}", "agreement": p_data['agreement'], "orig_data": p_data, "id": p_idx}

        # --- WRITERS ---
        for w_idx in range(1, 4):
            w_last = row.get(f'WRITER {w_idx}: Last Name')
            if pd.isna(w_last): continue
            
            w_first = pad(row.get(f'WRITER {w_idx}: First Name', ''), 30)
            w_ipi = pad(row.get(f'WRITER {w_idx}: IPI'), 11, True)
            w_pr = format_share(row.get(f'WRITER {w_idx}: Collection Performance Share %'))
            
            # SWR
            swr_seq = rec_seq # Capture sequence for PWR linking
            lines.append(f"SWR{t_seq:08d}{rec_seq:08d}00000000{w_idx}{pad(w_last, 45)}{w_first} C          {w_ipi}{w_pr}00000990000009900000 N")
            rec_seq += 1
            
            # SWT
            lines.append(f"SWT{t_seq:08d}{rec_seq:08d}00000000{w_idx}{w_pr}00000000000000I2136 001")
            rec_seq += 1
            
            # PWR
            orig_pub_name = str(row.get(f'WRITER {w_idx}: Original Publisher')).upper()
            linked_pub = next((v for k, v in pub_map.items() if k in orig_pub_name), None)
            
            if linked_pub:
                # The "Writer IP #" in PWR (Pos 116-124) must match the SWR Record Sequence? 
                # London Parity uses a specific ID logic here. We use the SWR row index relative to the transaction.
                # London Example: 000000001 (Writer 1), 000000002 (Writer 2).
                writer_ref_id = f"{w_idx:09d}" 
                lines.append(f"PWR{t_seq:08d}{rec_seq:08d}{linked_pub['chain']}00000000{linked_pub['id']}{pad(linked_pub['orig_data']['name'], 45)}{pad(linked_pub['agreement'], 14)}{writer_ref_id}")
                rec_seq += 1

        # --- ARTIFACTS ---
        cd_id = pad(row.get('ALBUM: Code', 'RC052'), 14)
        isrc = pad(row.get('CODE: ISRC', ''), 12)
        lines.append(f"REC{t_seq:08d}{rec_seq:08d}{now_d}{' '*54}000000{' '*80}{cd_id}{' '*10}{isrc}  CD{' '*103}RED COLA{' '*52}Y")
        rec_seq += 1
        lines.append(f"REC{t_seq:08d}{rec_seq:08d}{' '*68}000000{' '*94}{isrc}  DW {pad(row.get('TRACK: Title'), 60)}{' '*84}Y")
        rec_seq += 1
        lines.append(f"ORN{t_seq:08d}{rec_seq:08d}LIB{pad(row.get('ALBUM: Title'), 60).upper()}{cd_id}          0001RED COLA")

    lines.append(f"GRT00001{len(df):08d}{len(lines)+1:08d}")
    lines.append(f"TRL00001{len(df):08d}{len(lines)+1:08d}")
    
    return "\n".join(lines)
