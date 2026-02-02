import re

# ==============================================================================
# BUSINESS LOGIC CHECKS
# ==============================================================================

def check_business_logic(lines):
    logic_errors = []
    
    current_role = None
    current_pub_name = None
    
    for i, line in enumerate(lines):
        line_num = i + 1
        rec_type = line[0:3]
        
        # 1. REV CHECK (Work Type)
        if rec_type == "REV":
            # Vesna Rule: "ORI" at pos 142
            if len(line) > 144:
                work_type = line[142:145]
                if work_type != "ORI":
                     logic_errors.append({
                        "level": "WARNING", "line": line_num,
                        "message": f"MISSING 'ORI': Found '{work_type}' at 142. Vesna requires 'ORI'.",
                        "content": line
                    })
            
            # Duration Check
            duration = line[129:135] # Dynamic Blueprint pos
            if duration == "000000":
                 logic_errors.append({
                    "level": "WARNING", "line": line_num,
                    "message": "ZERO DURATION: Track duration is 00:00:00.",
                    "content": line
                })

        # 2. ADMIN SHARE CHECK
        if rec_type == "SPU":
            current_role = line[76:78].strip()
            current_pub_name = line[30:75].strip()
            
        if rec_type == "SPT":
            # Rule: If Administrator (SE), Mechanical/Sync share MUST be 100% (10000)
            if current_role == "SE":
                mr_share = line[39:44]
                sr_share = line[44:49]
                
                if mr_share != "10000":
                    logic_errors.append({
                        "level": "CRITICAL", "line": line_num,
                        "message": f"LOGIC FAIL: Admin '{current_pub_name}' has {mr_share} MR Share. Must be 10000 (100%).",
                        "content": line
                    })
                if sr_share != "10000":
                    logic_errors.append({
                        "level": "CRITICAL", "line": line_num,
                        "message": f"LOGIC FAIL: Admin '{current_pub_name}' has {sr_share} SR Share. Must be 10000 (100%).",
                        "content": line
                    })
                    
    return logic_errors

# ==============================================================================
# SYNTAX CHECKS
# ==============================================================================

PATTERNS = {
    "N": r"^\d+$",               
    "A": r"^[A-Z0-9\s\.,\-\']+$", 
    "X": r"^[A-Z0-9\s]+$",        
}

SCHEMA = {
    "HDR": [
        (0, 3, "A", "Record Type", True),
        (3, 11, "X", "Sender IPI", True),
        (59, 5, "A", "Version", True), 
    ],
    "REV": [ 
        (3, 8, "N", "Transaction Seq", True),
        (19, 60, "A", "Work Title", True),
    ],
    "SPU": [
        (3, 8, "N", "Transaction Seq", True),
        (11, 8, "N", "Record Seq", True),
        (30, 45, "A", "Publisher Name", True),
        (76, 2, "A", "Role Code", True),
    ],
    "PWR": [
        (3, 8, "N", "Transaction Seq", True),
        (19, 9, "X", "Publisher ID", True), 
        (28, 45, "A", "Publisher Name", True),
        (101, 11, "X", "Writer Reference", False) 
    ],
    "TRL": [
        (0, 3, "A", "Record Type", True),
        (8, 8, "N", "Transaction Count", True), 
        (16, 8, "N", "Record Count", True),     
    ]
}

class CWRValidator:
    def __init__(self):
        self.report = [] 
        self.stats = { "lines_read": 0, "transactions": 0 }
        self.current_t_seq = None

    def _log(self, level, line_num, message, raw_line=""):
        self.report.append({
            "level": level, "line": line_num,
            "message": message, "content": raw_line
        })

    def validate_field(self, value, f_type, f_name, line_num, mandatory):
        stripped_val = value.strip() 
        if mandatory and not stripped_val:
            return f"Missing mandatory field: {f_name}"
        if stripped_val:
            if f_type == "N" and not re.match(PATTERNS["N"], stripped_val):
                return f"Field '{f_name}' must be Numeric. Found: '{stripped_val}'"
        return None

    def process_file(self, file_content_str):
        lines = file_content_str.replace('\r\n', '\n').split('\n')
        lines = [l for l in lines if l.strip()] 
        
        self.stats["lines_read"] = len(lines)
        
        # 1. RUN BUSINESS LOGIC CHECK
        logic_errors = check_business_logic(lines)
        self.report.extend(logic_errors)
        
        # 2. RUN SYNTAX CHECK
        for i, line in enumerate(lines):
            line_num = i + 1
            if len(line) < 3: continue
            rec_type = line[0:3]
            
            if rec_type in ["NWR", "REV"]:
                self.stats["transactions"] += 1
                try: self.current_t_seq = int(line[3:11])
                except: self.current_t_seq = -1

            if rec_type in SCHEMA:
                rules = SCHEMA[rec_type]
                for start, length, f_type, f_name, mandatory in rules:
                    if len(line) < start + length:
                        if start < 10: 
                             self._log("ERROR", line_num, f"Line truncated. Missing {f_name}", line)
                        continue 
                        
                    val = line[start : start + length]
                    error = self.validate_field(val, f_type, f_name, line_num, mandatory)
                    if error:
                        self._log("ERROR", line_num, error, line)
            
            if rec_type == "TRL":
                try:
                    claimed_trans = int(line[8:16])
                    claimed_recs = int(line[16:24])
                    if claimed_trans != self.stats["transactions"]:
                        self._log("CRITICAL", line_num, f"Transaction Count Mismatch. Header says {claimed_trans}, Found {self.stats['transactions']}", line)
                    if claimed_recs != self.stats["lines_read"]:
                         self._log("CRITICAL", line_num, f"Total Record Count Mismatch. Header says {claimed_recs}, Found {self.stats['lines_read']}", line)
                except:
                     self._log("CRITICAL", line_num, "Trailer numeric parsing failed", line)

        return self.report, self.stats
