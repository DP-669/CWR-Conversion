import pandas as pd
from datetime import datetime
import math

# --- 1. CONFIGURATION & DATABASE ---
LUMINA_CONFIG = {
    "name": "LUMINA PUBLISHING UK",
    "ipi": "01254514077",
    "role": "SE",
    "territory": "0826"  # United Kingdom
}

# Master DB: Name match key -> {Official Name, IPI, Agreement}
PUBLISHER_DB = {
    "TARMAC": {"name": "TARMAC 1331 PUBLISHING", "ipi": "00356296239", "agreement": "6781310"},
    "PASHALINA": {"name": "PASHALINA PUBLISHING", "ipi": "00498578867", "agreement": "4316161"},
    "MANNY": {"name": "MANNY G MUSIC", "ipi": "00515125979", "agreement": "13997451"},
    "SNOOPLE": {"name": "SNOOPLE SONGS", "ipi": "00610526488", "agreement": "13990221"}
}

# --- 2. FORMATTING HELPERS ---
def pad(val, length, is_num=False):
    """Ensures fixed-width CWR compliance."""
    if pd.isna(val): val = ""
    val = str(val).strip().upper()
    
    # Remove floats decimals if it's an integer field (like IPI)
    if is_num and val.endswith('.0'):
        val = val[:-2]
        
    return val.zfill(length) if is_num else val.ljust(length)[:length]

def format_share(val):
    """
    Converts float percentage (16.5) to CWR 5-digit (01650).
    Handles NaNs and string formatting.
    """
    try:
        if pd.isna(val) or str(val).strip() == '':
            return "00000"
        f_val = float(val)
        return f"{int(round(f_val * 100)):05d}"
    except:
        return "00000"

def get_pub_data(raw_name):
    """Finds publisher in DB or returns defaults."""
    raw = str(raw_name).upper()
    for key, data in PUBLISHER_DB.items():
        if key in raw:
            return data
    return {"name": pad(raw_name, 45), "ipi": "00000000000", "agreement": "00000000"}

# --- 3. GENERATION LOGIC ---
def generate_cwr_content(df):
    lines = []
    now_d = datetime.now().strftime("%Y%m%d")
    now_t = datetime.now().strftime("%H%M%S")
    
    # HEADER
    # Matches Parity: HDR + IPI(11) + Name(45) + 01.10 + Date/Time...
    lines.append(f"HDR{pad(LUMINA_CONFIG['ipi'], 11)}LUMINA PUBLISHING UK                         01.10{now_d}{now_t}{now_d}               2.2001BACKBEAT")
    lines.append("GRHREV0000102.200000000001")

    # TRANSACTION LOOP
    for i, row in df.iterrows():
        # Transaction Sequence (Matches Parity 0-based index or 1-based? Parity showed 00000000)
        # We use i (0-based) to match Parity snippet exactly, change to i+1 if ICE rejects.
        t_seq = i 
        
        # --- METADATA ---
        # "CODE: ISWC" or "Song_Number" or "TRACK: Number"
        raw_work_id = row.get('Song_Number')
        if pd.isna(raw_work_id):
            raw_work_id = row.get('CODE: Song Code')
        if pd.isna(raw_work_id):
             # Fallback to Track Number padded if no ID exists
            raw_work_id = f"{int(row.get('TRACK: Number', 0)):07d}" if pd.notna(row.get('TRACK: Number')) else "0000000"

        submitter_id = pad(raw_work_id, 14) 
        title = pad(row.get('TRACK: Title', 'UNKNOWN TITLE'), 60)
        duration = "000000" # Parity default, or map from TRACK: Duration if needed
        if 'TRACK: Duration' in df.columns:
            try:
                # Convert seconds to HHMMSS? Parity showed 0003606 for 25s??
                # We will stick to 000000 unless specified.
                pass
            except: pass

        iswc = pad(row.get('CODE: ISWC', ''), 11)
        if not iswc.startswith('T'): iswc = '           ' # Blank if no valid ISWC

        # REV RECORD
        # Note: Parity has 0003606 in the ID field position. We use submitter_id there.
        lines.append(f"REV{t_seq:08d}00000000{title}   {submitter_id}{iswc}00000000UNC000025Y      ORI{' '*52}00000000000{' '*51}Y")

        # --- PUBLISHER CHAINS ---
        # We scan PUBLISHER 1, 2, 3...
        # Each Publisher creates a chain: [SPU Orig] -> [SPU Lumina] -> [SPT UK]
        
        pub_map = {} # Map 'Chain ID' -> Original Publisher Data (for PWR linking)
        rec_seq = 1
        
        for p_idx in range(1, 4): # Loop Publisher 1 to 3
            p_name = row.get(f'PUBLISHER {p_idx}: Name')
            if pd.isna(p_name): continue
            
            p_data = get_pub_data(p_name)
            p_share_pr = format_share(row.get(f'PUBLISHER {p_idx}: Collection Performance Share %'))
            p_share_mr = format_share(row.get(f'PUBLISHER {p_idx}: Collection Mechanical Share %'))
            
            # Chain ID matches Publisher Index (01, 02, 03)
            chain_id = f"{p_idx:02d}"
            
            # SPU 1: Original Publisher (Role E)
            # Parity: 021(PR) 021(MR) 03300(SR?)
            # We map PR and MR. SR (Sync) often matches MR or PR. Parity used 33.0 for Sync (03300)
            lines.append(f"SPU{t_seq:08d}{rec_seq:08d}{chain_id}00000000{p_idx}{pad(p_data['name'], 45)}E          {pad(p_data['ipi'], 11, True)}              021{p_share_pr}021{p_share_mr}   {p_share_mr} N{' '*28}{pad(p_data['agreement'], 14)}PG")
            rec_seq += 1
            
            # SPU 2: Lumina (Role SE)
            # Parity Share Logic: 05200000 (Admin?), 03300000 (Mech?), 03300000 (Sync?)
            # Lumina gets 0% in PR? Parity file showed 00000 for Lumina shares in SPU line.
            lines.append(f"SPU{t_seq:08d}{rec_seq:08d}{chain_id}000000012{pad(LUMINA_CONFIG['name'], 45)}{LUMINA_CONFIG['role']}         {pad(LUMINA_CONFIG['ipi'], 11, True)}              052000000330000003300000 N{' '*28}{pad(p_data['agreement'], 14)}PG")
            rec_seq += 1
            
            # SPT: Territory (UK)
            # Parity: 01650 (PR), 03300 (MR), 03300 (SR) -> Matches Original Publisher shares? 
            # Parity uses 'I0826' (Include UK)
            lines.append(f"SPT{t_seq:08d}{rec_seq:08d}{p_share_pr}{p_share_mr}{p_share_mr}I{LUMINA_CONFIG['territory']} 001")
            rec_seq += 1
            
            # Store for PWR linking
            pub_map[p_data['name']] = {"chain": chain_id, "agreement": p_data['agreement'], "orig_data": p_data, "id": p_idx}

        # --- WRITER LOOP ---
        for w_idx in range(1, 4):
            w_last = row.get(f'WRITER {w_idx}: Last Name')
            if pd.isna(w_last): continue
            
            w_first = row.get(f'WRITER {w_idx}: First Name', '')
            w_ipi = pad(row.get(f'WRITER {w_idx}: IPI'), 11, True)
            w_role = "C " # Default Composer
            
            # Shares
            w_pr = format_share(row.get(f'WRITER {w_idx}: Collection Performance Share %'))
            w_mr = format_share(row.get(f'WRITER {w_idx}: Collection Mechanical Share %'))
            
            # SWR
            # Parity: 021(PR) 09900000 (MR 0?) 09900000 (SR 0?)
            # Parity showed MR/SR as 00000 with status 99? Or status 0?
            # Parity: 021 01650 099 00000 099 00000
            lines.append(f"SWR{t_seq:08d}{rec_seq:08d}00000000{w_idx}{pad(w_last, 45)}{pad(w_first, 30)} {w_role}          {w_ipi}{w_pr}00000990000009900000 N")
            rec_seq += 1
            
            # SWT (World 2136)
            lines.append(f"SWT{t_seq:08d}{rec_seq:08d}00000000{w_idx}{w_pr}00000000000000I2136 001")
            rec_seq += 1
            
            # PWR (Link Writer to Publisher)
            # Find which publisher controls this writer
            orig_pub_name = str(row.get(f'WRITER {w_idx}: Original Publisher')).upper()
            
            # Lookup in our pub_map
            linked_pub = next((v for k, v in pub_map.items() if k in orig_pub_name), None)
            
            if linked_pub:
                # PWR Record
                # Parity: PWR... PubName... Agr... WriterIP# (000000001)
                # Writer IP# here refers to the SWR sequence (000000001 for Writer 1)
                writer_seq_ref = f"{w_idx:09d}" # 000000001
                lines.append(f"PWR{t_seq:08d}{rec_seq:08d}{linked_pub['chain']}00000000{linked_pub['id']}{pad(linked_pub['orig_data']['name'], 45)}{pad(linked_pub['agreement'], 14)}{writer_seq_ref}01")
                rec_seq += 1

        # --- RECORDS & ORIGIN ---
        cd_id = pad(row.get('ALBUM: Code', 'RC052'), 14)
        isrc = pad(row.get('CODE: ISRC', ''), 12)
        lib = pad(row.get('LIBRARY: Name', 'RED COLA'), 60)
        
        lines.append(f"REC{t_seq:08d}{rec_seq:08d}{now_d}{' '*54}000000{' '*80}{cd_id}{' '*10}{isrc}  CD{' '*103}RED COLA{' '*52}Y")
        rec_seq += 1
        lines.append(f"ORN{t_seq:08d}{rec_seq:08d}LIB{lib}{cd_id}0254RED COLA")

    # TRAILERS
    lines.append(f"GRT00001{len(df):08d}{len(lines)+1:08d}")
    lines.append(f"TRL00001{len(df):08d}{len(lines)+1:08d}")
    
    return "\n".join(lines)
