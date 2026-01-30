import re

# ==============================================================================
# LAYER 1: THE LAWS (CONFIGURATION & SCHEMA)
# ==============================================================================

# Regex Patterns for Data Types
PATTERNS = {
    "N": r"^\d+$",              # Numeric (Integer)
    "A": r"^[A-Z0-9\s\.,]+$",   # Alpha-Numeric (Basic)
    "D": r"^\d{8}$",            # Date YYYYMMDD
    "T": r"^\d{6}$",            # Time HHMMSS
    "B": r"^[A-Z\s]*$"          # Boolean/Flag (Usually Y/N/Space)
}

# Critical Field Definitions (Start, Length, Type, Name, Mandatory?)
# We focus on the fields that break ingestion if wrong.
SCHEMA = {
    "HDR": [
        (0, 3, "A", "Record Type", True),
        (3, 11, "N", "Sender IPI", True),
        (59, 5, "A", "Version", True), # e.g. 02.10
    ],
    "NWR": [
        (3, 8, "N", "Transaction Seq", True),
        (19, 60, "A", "Work Title", True),
        (95, 11, "A", "ISWC", False), # Conditional, but we check format if present
    ],
    "REV": [ # Same structural requirements as NWR usually
        (3, 8, "N", "Transaction Seq", True),
        (19, 60, "A", "Work Title", True),
    ],
    "SPU": [
        (3, 8, "N", "Transaction Seq", True),
        (18, 9, "N", "Publisher Seq", True),
        (27, 2, "A", "Publisher Role", True), # E, AM, SE
        (29, 45, "A", "Publisher Name", True),
    ],
    "PWR": [
        (3, 8, "N", "Transaction Seq", True),
        (18, 9, "N", "Writer Seq", True),
        (27, 45, "A", "Writer Last Name", True),
        (117, 11, "N", "Writer IPI", False), 
    ],
    "TRL": [
        (0, 3, "A", "Record Type", True),
        (3, 8, "N", "Group Count", True),
        (11, 8, "N", "Transaction Count", True),
        (19, 8, "N", "Record Count", True),
    ]
}

# ==============================================================================
# LAYER 2: THE DETECTIVE (LOGIC ENGINE)
# ==============================================================================

class CWRValidator:
    def __init__(self):
        self.report = [] # List of errors/warnings
        self.stats = {
            "lines_read": 0,
            "transactions": 0, # Count of NWR/REV
            "groups": 0,       # GRH (Not always used in V2.1 minimal, but tracked)
        }
        self.current_t_seq = None

    def _log(self, level, line_num, message, raw_line=""):
        self.report.append({
            "level": level, # ERROR, WARNING, INFO
            "line": line_num,
            "message": message,
            "content": raw_line
        })

    def validate_field(self, value, f_type, f_name, line_num, mandatory):
        """Validates a single substring against its type definition."""
        value = value.strip() # CWR is padded, so we strip for value checking
        
        if mandatory and not value:
            return f"Missing mandatory field: {f_name}"
            
        if value:
            if f_type == "N" and not re.match(PATTERNS["N"], value):
                return f"Field '{f_name}' must be Numeric. Found: '{value}'"
            if f_type == "D" and not re.match(PATTERNS["D"], value):
                return f"Field '{f_name}' must be Date (YYYYMMDD). Found: '{value}'"
                
        return None

    def process_file(self, file_content_str):
        """Main execution entry point."""
        lines = file_content_str.split('\n')
        # Remove empty lines at end of file if any
        lines = [l for l in lines if l.strip()]
        
        self.stats["lines_read"] = len(lines)
        
        # 1. Structural Scan
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # A. Line Length (Strict CWR is usually fixed, but V2.1 can vary. 
            # We enforce a safe minimum to prevent index errors).
            if len(line) < 3:
                self._log("CRITICAL", line_num, "Line too short to be valid record", line)
                continue

            # B. Record Type lookup
            rec_type = line[0:3]
            
            # Logic: Transaction Counter
            if rec_type in ["NWR", "REV"]:
                self.stats["transactions"] += 1
                try:
                    self.current_t_seq = int(line[3:11])
                except:
                    self.current_t_seq = "INVALID"

            # Logic: Group Counter
            if rec_type == "GRH":
                self.stats["groups"] += 1

            # C. Schema Validation
            if rec_type in SCHEMA:
                rules = SCHEMA[rec_type]
                for start, length, f_type, f_name, mandatory in rules:
                    # Guard against line being shorter than expected field
                    if len(line) < start + length:
                        self._log("ERROR", line_num, f"Line too short for field '{f_name}'", line)
                        continue
                        
                    val = line[start : start + length]
                    error = self.validate_field(val, f_type, f_name, line_num, mandatory)
                    if error:
                        self._log("ERROR", line_num, error, line)
            
            # D. Hierarchy Integrity (Transaction Sequence Check)
            # If we are inside a transaction (SPU, PWR, etc), check if T_SEQ matches parent
            if rec_type in ["SPU", "SPT", "PWR", "SWT", "OPU"]:
                if self.current_t_seq == "INVALID":
                     self._log("ERROR", line_num, "Orphaned Record (Parent Transaction Invalid)", line)
                else:
                    try:
                        line_t_seq = int(line[3:11])
                        if line_t_seq != self.current_t_seq:
                            self._log("ERROR", line_num, f"Sequence Mismatch. Expected {self.current_t_seq}, got {line_t_seq}", line)
                    except:
                        self._log("ERROR", line_num, "Non-numeric Transaction Sequence", line)

            # E. Trailer Validation (The "Checksum")
            if rec_type == "TRL":
                try:
                    claimed_trans = int(line[11:19])
                    claimed_recs = int(line[19:27])
                    
                    if claimed_trans != self.stats["transactions"]:
                        self._log("CRITICAL", line_num, f"Transaction Count Mismatch. Header says {claimed_trans}, Found {self.stats['transactions']}", line)
                    
                    if claimed_recs != self.stats["lines_read"]:
                         self._log("CRITICAL", line_num, f"Total Record Count Mismatch. Header says {claimed_recs}, Found {self.stats['lines_read']}", line)
                         
                except ValueError:
                     self._log("CRITICAL", line_num, "Trailer numeric parsing failed", line)

        return self.report, self.stats
