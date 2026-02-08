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
    HDR = [
        (0, 3, "HDR"), (3, 2, "01"), (5, 11, "{sender_ipi}"), 
        (16, 45, "{sender_name}"), (61, 5, "01.10"), (66, 8, "{date}"), 
        (74, 6, "{time}"), (80, 8, "{date}"), (103, 3, "2.2"), (106, 2, "00")
    ]
    GRH = [(0, 3, "GRH"), (3, 3, "NWR"), (6, 5, "00001"), (11, 5, "02.10"), (16, 10, "0000000000")]
    REV = [
        (0, 3, "REV"), (3, 8, "{t_seq}"), (11, 8, "00000000"), (19, 60, "{title}"), 
        (79, 2, "  "), (81, 14, "{work_id}"), (95, 11, "{iswc}"), (106, 8, "00000000"), 
        (126, 3, "UNC"), (129, 6, "{duration}"), (135, 1, "Y"), (136, 6, "      "), (142, 3, "ORI")
    ]
    SPU = [
        (0, 3, "SPU"), (3, 8, "{t_seq}"), (11, 8, "{rec_seq}"), (19, 2, "{chain_id}"), 
        (21, 9, "{pub_id}"), (30, 45, "{pub_name}"), (76, 2, "{role}"), (87, 11, "{ipi}"), 
        (98, 14, "{agreement}"), (112, 3, "{pr_soc}"), (115, 5, "{pr_share}"), 
        (120, 3, "{mr_soc}"), (123, 5, "{mr_share}"), (128, 3, "{sr_soc}"), 
        (131, 5, "{sr_share}"), (136, 1, "N"), (165, 14, "{agreement}"), (179, 2, "PG")
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
        (145, 5, "{sr_share}"), (150, 1, "N")
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

def
