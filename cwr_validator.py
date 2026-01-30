import re

# ==============================================================================
# LAYER 1: THE LAWS (ALIGNED TO ICE "BIBLE" FILES)
# ==============================================================================

PATTERNS = {
    "N": r"^\d+$",                # Strict Numeric
    "A": r"^[A-Z0-9\s\.,\-\']+$", # Alphanumeric (Names, Titles)
    "X": r"^[A-Z0-9\s]+$",        # IDs (Allows "SO...", "SN..." prefixes found in ICE files)
}

# SCHEMA DEFINITION
# Format: (start_index, length, pattern_key, field_name, is_mandatory)
# Offsets verified against 'CW250011052_LUM.V22.txt'

SCHEMA = {
    "HDR": [
        (0, 3, "A", "Record Type", True),
        (3, 11, "X", "Sender IPI", True), # Changed to X to allow "SO" prefix
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
        # NOTE: ICE Files skip the 'Chain ID' at 19-21. 
        # Publisher ID starts immediately at 19.
        (3, 8, "N", "Transaction Seq", True),
        (19, 9, "X", "Publisher ID", True), # Starts at 19 (not 21)
        (28, 45, "A", "Publisher Name", True), # Starts at 28 (not 30)
    ],
    "TRL": [
        (0, 3, "A", "Record Type", True),
        (11, 8, "N", "Transaction Count", True), 
        (19, 8, "N", "Record Count", True),
    ]
}

# ==============================================================================
# LAYER 2: THE DETECTIVE (LOGIC ENGINE)
# ==============================================================================

class CWRValidator:
    def __init__(self):
        self.report = [] 
        self.stats = {
            "lines_read": 0,
            "transactions": 0, 
        }
        self.current_t_seq = None

    def _log(self, level, line_num, message, raw_line=""):
        self.report.append({
            "level": level, 
            "line": line_num,
            "message": message,
            "content": raw_line
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
        # Normalize line endings
        lines = file_content_str.replace('\r\n', '\n').split('\n')
        lines = [l for l in lines if l.strip()] # Remove empty lines
        
        self.stats["lines_read"] = len(lines)
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            if len(line) < 3: continue
            rec_type = line[0:3]
            
            # Logic: Transaction Counter
            if rec_type in ["NWR", "REV"]:
                self.stats["transactions"] += 1
                try: self.current_t_seq = int(line[3:11])
                except: self.current_t_seq = -1

            # Schema Validation
            if rec_type in SCHEMA:
                rules = SCHEMA[rec_type]
                for start, length, f_type, f_name, mandatory in rules:
                    # Skip check if line is simply too short (truncation is common in CWR)
                    if len(line) < start + length: continue
                        
                    val = line[start : start + length]
                    error = self.validate_field(val, f_type, f_name, line_num, mandatory)
                    if error:
                        self._log("ERROR", line_num, error, line)
            
            # Hierarchy Check (Sequence Integrity)
            if rec_type not in ["HDR", "TRL", "GRH", "GRT"] and rec_type in SCHEMA:
                 try:
                    line_t_seq = int(line[3:11])
                    if self.current_t_seq != -1 and line_t_seq != self.current_t_seq:
                        self._log("ERROR", line_num, f"Sequence Mismatch. Expected {self.current_t_seq}, got {line_t_seq}", line)
                 except: pass

            # Trailer Check
            if rec_type == "TRL":
                try:
                    claimed_trans = int(line[11:19])
                    claimed_recs = int(line[19:27])
                    
                    if claimed_trans != self.stats["transactions"]:
                        self._log("CRITICAL", line_num, f"Transaction Count Mismatch. Header says {claimed_trans}, Found {self.stats['transactions']}", line)
                    
                    if claimed_recs != self.stats["lines_read"]:
                         self._log("CRITICAL", line_num, f"Total Record Count Mismatch. Header says {claimed_recs}, Found {self.stats['lines_read']}", line)
                except:
                     self._log("CRITICAL", line_num, "Trailer numeric parsing failed", line)

        return self.report, self.stats
