import pandas as pd
from datetime import datetime
import re

# ==============================================================================
# CONFIGURATION
# ==============================================================================
LUMINA_CONFIG = {
    "name": "LUMINA PUBLISHING UK",
    "ipi": "01254514077",
    "territory": "0826"
}

AGREEMENT_MAP = {
    "PASHALINA": "4316161", "LUKACINO": "3845006", "TARMAC": "6781310",
    "SNOOPLE": "13990221", "MANNY": "13997451", "REDCOLA": "4165777",
    "HOLLY PALMER": "13994635", "DEMENTIA": "13994638", "CULVERTOWN": "13994260",
    "VANTABLACK": "13994073", "TORO ROSSO": "13994607", "MINA": "13995081",
    "MC TROUBLE": "13996234"
}

class Assembler:
    def __init__(self):
        self.buffer = [' '] * 512
    def build(self, blueprint, data_dict):
        self.buffer = [' '] * 512 
        for start, length, value_template in blueprint:
            if value_template.startswith("{") and value_template.endswith("}"):
                key = value_template[1:-1]
                val = data_dict.get(key, "")
            else:
                val = value_template
            if val is None or str(val).strip().upper() in ['NAN', 'NONE', '']:
                val = ""
            val = str(val).strip().upper()
            padded_val = val.ljust(length)[:length]
            for i, char in enumerate(padded_val):
                if start + i < 512:
                    self.buffer[start + i] = char
        return "".join(self.buffer).rstrip()

class Blueprints:
    # FIXED: Sender Name shifted to 14 to eliminate double space after 9-digit IPI
    HDR = [
        (0, 3, "HDR"), (3, 2, "01"), (5, 9, "{sender_ipi_short}"), 
        (14, 45, "{sender_name}"), (61, 5, "01.10"), (66, 8, "{date}"), 
        (74, 6, "{time}"), (80, 8, "{date}"), (103, 3, "2.2"), (106, 2, "00")
    ]
    GRH = [(0, 3, "GRH"), (3, 3, "NWR"), (6, 5, "00001"), (11, 5, "02.10"), (16, 10, "0000000000")]
    
    # FIXED: Changed from REV to NWR to match Group Header
    NWR = [
        (0, 3, "NWR"), (3, 8, "{t_seq}"), (11, 8, "00000000"), (19, 60, "{title}"), 
        (79, 2, "  "), (81, 14, "{work_id}"), (95, 11, "{iswc}"), (106, 8, "00000000"), 
        (126, 3, "UNC"), (129, 6, "{duration}"), (135, 1, "Y"), (136, 6, "      "), (142, 3, "ORI")
    ]
    
    SPU = [
        (0, 3, "SPU"), (3, 8, "{t_seq}"), (11, 8, "{rec_seq}"), (19, 2, "{chain_id}"), 
        (21, 9, "{pub_id}"), (30, 45, "{pub_name}"), (76, 2, "{role}"), (87, 11, "{ipi}"), 
        (112, 3, "{pr_soc}"), (115, 5, "{pr_share}"), 
        (120, 3, "{mr_soc}"), (123, 5, "{mr_share}"), (128, 3, "{sr_soc}"), 
        (131, 5, "{sr_share}"), (137, 1, "N"), (165, 14, "{agreement}"), (179, 2, "PG"),
        (181, 3, "   ")
    ]
    SPT = [
        (0, 3, "SPT"), (3, 8, "{t_seq}"), (11, 8, "{rec_seq}"), (19, 9, "{pub_id}"), 
        (34, 5, "{pr_share}"), (39, 5, "{mr_share}"), (44, 5, "{sr_share}"), 
        (49, 1, "I"), (50, 4, "{territory}"), (55, 3, "001")
    ]
    SWR = [
        (0, 3, "SWR"), (3, 8, "{t_seq}"), (11, 8, "{rec_seq}"), (19, 9, "{writer_id}"), 
        (28, 45, "{last_name}"), (73, 30, "{first_name}"), (104, 2, "C "), 
        (115, 11, "{ipi}"), (126, 3, "{pr_soc}"), (129, 5, "{pr_share}"), 
        (134, 3, "{mr_soc}"), (137, 5, "{mr_share}"), (142, 3, "{sr_soc}"), 
        (145, 5, "{sr_share}"), (151, 1, "N")
    ]
    SWT = [
        (0, 3, "SWT"), (3, 8, "{t_seq}"), (11, 8, "{rec_seq}"), (19, 9, "{writer_id}"), 
        (28, 5, "{pr_share}"), (33, 5, "{mr_share}"), (38, 5, "{sr_share}"), 
        (43, 1, "I"), (44, 4, "2136"), (49, 3, "001")
    ]
    PWR = [
        (0, 3, "PWR"), (3, 8, "{t_seq}"), (11, 8, "{rec_seq}"), (19, 9, "{pub_id}"), 
        (28, 45, "{pub_name}"), (73, 14, "{agreement}"), (101, 9, "{writer_id}"), (110, 2, "{chain_id}")
    ]
    REC = [
        (0, 3, "REC"), (3, 8, "{t_seq}"), (11, 8, "{rec_seq}"), (19, 8, "00000000"), 
        (74, 6, "{duration}"), (154, 14, "{cd_id}"), (180, 12, "{isrc}"), 
        (194, 2, "{source}"), (197, 60, "{title}"), (297, 60, "{label}"), (349, 1, "Y")
    ]
    ORN = [
        (0, 3, "ORN"), (3, 8, "{t_seq}"), (11, 8, "{rec_seq}"), (19, 3, "LIB"), 
        (22, 60, "{library}"), (82, 14, "{cd_id}"), (96, 4, "0001"), (100, 60, "{label}")
    ]
    GRT = [(0, 3, "GRT"), (3, 5, "00001"), (8, 8, "{t_count}"), (16, 8, "{r_count}")]
    TRL = [(0, 3, "TRL"), (3, 5, "00001"), (8, 8, "{t_count}"), (16, 8, "{r_count}")]

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
            parts = v.split(":"); m, s = int(parts[0]), int(parts[1]); h = 0
        else:
            ts = int(float(v)); m, s = divmod(ts, 60); h, m = divmod(m, 60)
        return f"{h:02d}{m:02d}{s:02d}"
    except: return "000000"

def get_vessel_col(row, base, idx, suffix):
    target = f"{base}:{idx}: {suffix}".strip().upper()
    for col in row.index:
        if target in str(col).upper(): return row[col]
    return None

def generate_cwr_content(df):
    lines = []; asm = Assembler(); now = datetime.now()
    
    full_ipi = pad_ipi(LUMINA_CONFIG["ipi"])
    hdr_ipi = full_ipi[-9:] 
    
    lines.append(asm.build(Blueprints.HDR, {
        "sender_ipi_short": hdr_ipi, 
        "sender_name": LUMINA_CONFIG["name"], 
        "date": now.strftime("%Y%m%d"), 
        "time": now.strftime("%H%M%S")
    }))
    lines.append(asm.build(Blueprints.GRH, {}))
    t_count = 0; r_sum = 2 
    for i, row in df.iterrows():
        t_count += 1; t_seq = f"{(t_count-1):08d}"; rec_seq = 1; pub_map = {}
        title_val = str(row.get('TRACK: Title', 'UNKNOWN'))
        # FIXED: Switched from REV to NWR blueprint
        lines.append(asm.build(Blueprints.NWR, {"t_seq": t_seq, "title": title_val, "work_id": str(row.get('TRACK: Number', i+1)), "iswc": str(row.get('CODE: ISWC', '')), "duration": parse_duration(row.get('TRACK: Duration', '0'))}))
        rec_sum_in_t = 1
        for p_idx in range(1, 4):
            p_name = get_vessel_col(row, "PUBLISHER", p_idx, "Name")
            if not p_name or pd.isna(p_name) or str(p_name).upper() == 'NAN': continue
            p_name = str(p_name).strip(); agr = "00000000"
            for k, v in AGREEMENT_MAP.items():
                if k in p_name.upper(): agr = v; break
            pr_raw = get_vessel_col(row, "PUBLISHER", p_idx, "Owner Performance Share %")
            
            cwr_share = float(pr_raw) if pd.notna(pr_raw) else 0.0
            
            lines.append(asm.build(Blueprints.SPU, {"t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "chain_id": f"{p_idx:02d}", "pub_id": f"00000000{p_idx}", "pub_name": p_name, "role": "E ", "ipi": pad_ipi(get_vessel_col(row, "PUBLISHER", p_idx, "IPI")), "pr_soc": "021", "mr_soc": "021", "sr_soc": "   ", "pr_share": fmt_share(cwr_share), "mr_share": "10000", "sr_share": "10000", "agreement": agr}))
            rec_seq += 1; rec_sum_in_t += 1
            lum_id = "000000012"
            lines.append(asm.build(Blueprints.SPU, {"t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "chain_id": f"{p_idx:02d}", "pub_id": lum_id, "pub_name": LUMINA_CONFIG['name'], "role": "SE", "ipi": pad_ipi(LUMINA_CONFIG['ipi']), "pr_soc": "052", "mr_soc": "033", "sr_soc": "033", "pr_share": "00000", "mr_share": "00000", "sr_share": "00000", "agreement": agr}))
            rec_seq += 1; rec_sum_in_t += 1
            lines.append(asm.build(Blueprints.SPT, {"t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "pub_id": lum_id, "pr_share": fmt_share(cwr_share), "mr_share": "10000", "sr_share": "10000", "territory": LUMINA_CONFIG['territory']}))
            rec_seq += 1; rec_sum_in_t += 1
            pub_map[p_name.upper()] = {"chain": f"{p_idx:02d}", "id": f"00000000{p_idx}", "agr": agr}
        for w_idx in range(1, 4):
            w_last = get_vessel_col(row, "WRITER", w_idx, "Last Name")
            if not w_last or pd.isna(w_last) or str(w_last).upper() == 'NAN': continue
            w_pr_raw = get_vessel_col(row, "WRITER", w_idx, "Owner Performance Share %")
            
            c_w_share = float(w_pr_raw) if pd.notna(w_pr_raw) else 0.0
            
            lines.append(asm.build(Blueprints.SWR, {"t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "writer_id": f"00000000{w_idx}", "last_name": str(w_last), "first_name": str(get_vessel_col(row, "WRITER", w_idx, "First Name") or ""), "ipi": pad_ipi(get_vessel_col(row, "WRITER", w_idx, "IPI")), "pr_soc": "021", "mr_soc": "099", "sr_soc": "099", "pr_share": fmt_share(c_w_share), "mr_share": "00000", "sr_share": "00000"})); rec_seq += 1; rec_sum_in_t += 1
            lines.append(asm.build(Blueprints.SWT, {"t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "writer_id": f"00000000{w_idx}", "pr_share": fmt_share(c_w_share), "mr_share": "00000", "sr_share": "00000"})); rec_seq += 1; rec_sum_in_t += 1
            orig_pub_name = str(get_vessel_col(row, "WRITER", w_idx, "Original Publisher") or "").strip().upper()
            if orig_pub_name in pub_map:
                p_i = pub_map[orig_pub_name]
                lines.append(asm.build(Blueprints.PWR, {"t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "pub_id": p_i['id'], "pub_name": orig_pub_name[:45], "agreement": p_i['agr'], "writer_id": f"00000000{w_idx}", "chain_id": p_i['chain']})); rec_seq += 1; rec_sum_in_t += 1
        isrc_v = str(row.get('CODE: ISRC', '')); cd_v = str(row.get('ALBUM: Code', 'RC055'))
        lines.append(asm.build(Blueprints.REC, {"t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "isrc": isrc_v, "cd_id": cd_v, "source": "CD", "title": "", "label": "RED COLA", "duration": parse_duration(row.get('TRACK: Duration', '0'))})); rec_seq += 1; rec_sum_in_t += 1
        lines.append(asm.build(Blueprints.ORN, {"t_seq": t_seq, "rec_seq": f"{rec_seq:08d}", "library": "RED COLA", "cd_id": cd_v, "label": "RED COLA"})); rec_seq += 1; rec_sum_in_t += 1
        r_sum += rec_sum_in_t
    lines.append(asm.build(Blueprints.GRT, {"t_count": f"{t_count:08d}", "r_count": f"{(r_sum+1):08d}"}))
    lines.append(asm.build(Blueprints.TRL, {"t_count": f"{t_count:08d}", "r_count": f"{(r_sum+3):08d}"}))
    return "\n".join(lines)
