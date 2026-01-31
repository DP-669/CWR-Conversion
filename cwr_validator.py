import re

# ==============================================================================
# LAYER 1: THE LAWS (ALIGNED TO YOUR 'CW25...' FILE)
# ==============================================================================

PATTERNS = {
    "N": r"^\d+$",                # Strict Numeric
    "A": r"^[A-Z0-9\s\.,\-\']+$", # Alphanumeric
    "X": r"^[A-Z0-9\s]+$",        # IDs (Allows "SO...", "SN..." prefixes)
}

# SCHEMA: (start_index, length, pattern_key, field_name, is_mandatory)
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
        # FIXED: Removed 'Writer IPI' check which caused "Line too short"
        (3, 8, "N", "Transaction Seq", True),
        (19, 9, "X", "Publisher ID", True), 
        (28, 45, "A", "Publisher Name", True),
        (101, 11, "X", "Writer Reference", False) # Ends around 112
    ],
    "TRL": [
        # FIXED: Offsets adjusted for 5-digit Group ID
        (0, 3, "A", "Record Type", True),
        (8, 8, "N", "Transaction Count", True), # Starts at 8 (TRL + 5 digit Group)
        (16, 8, "N", "Record Count", True),     # Starts at 16
    ]
}

# ==============================================================================
# LAYER 2: THE DETECTIVE
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
        # Normalize line endings to prevent ghost lines
        lines = file_content_str.replace('\r\n', '\n').split('\n')
        lines = [l for l in lines if l.strip()] 
        
        self.stats["lines_read"] = len(lines)
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Skip extremely short garbage lines
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
                    # SAFETY: If line is too short for this field, skip it 
                    # (unless it's the very start of the line, which is critical)
                    if len(line) < start + length:
                        if start < 10: # Critical header fields must exist
                             self._log("ERROR", line_num, f"Line truncated. Missing {f_name}", line)
                        continue 
                        
                    val = line[start : start + length]
                    error = self.validate_field(val, f_type, f_name, line_num, mandatory)
                    if error:
                        self._log("ERROR", line_num, error, line)
            
            # Trailer Check (Corrected Logic)
            if rec_type == "TRL":
                try:
                    # Using the offsets defined in SCHEMA['TRL'] above (8 and 16)
                    claimed_trans = int(line[8:16])
                    claimed_recs = int(line[16:24])
                    
                    if claimed_trans != self.stats["transactions"]:
                        self._log("CRITICAL", line_num, f"Transaction Count Mismatch. Header says {claimed_trans}, Found {self.stats['transactions']}", line)
                    
                    if claimed_recs != self.stats["lines_read"]:
                         self._log("CRITICAL", line_num, f"Total Record Count Mismatch. Header says {claimed_recs}, Found {self.stats['lines_read']}", line)
                except:
                     self._log("CRITICAL", line_num, "Trailer numeric parsing failed", line)

        return self.report, self.stats
