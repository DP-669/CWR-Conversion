import re

class CWRValidator:
    def process_file(self, content):
        lines = content.replace('\r\n', '\n').split('\n')
        report = []
        stats = {"lines_read": len(lines), "transactions": 0}
        
        current_work = None
        has_writer = False
        has_publisher = False

        for i, line in enumerate(lines):
            l_num = i + 1
            if len(line) < 3: continue
            rec = line[0:3]

            # --- COMPLETENESS CHECK ---
            if rec == "REV" or rec == "TRL":
                if current_work:
                    if not has_writer:
                        report.append({"level": "CRITICAL", "line": l_num-1, "message": f"WORK '{current_work}' HAS NO WRITERS.", "content": ""})
                    if not has_publisher:
                        report.append({"level": "CRITICAL", "line": l_num-1, "message": f"WORK '{current_work}' HAS NO PUBLISHERS.", "content": ""})
                
                if rec == "REV":
                    current_work = line[19:79].strip()
                    has_writer = False; has_publisher = False
                    stats["transactions"] += 1

            # --- DATA PRESENCE ---
            if rec == "SWR": has_writer = True
            if rec == "SPU": has_publisher = True

            # --- GEOMETRY & SYNTAX AUDIT ---
            # 1. "NAN" Check (Smart): Only fails if NAN is a standalone word or in an ID field
            # We look for " NAN " (space padded) or "NAN" at start/end of a field
            if "NAN" in line:
                # Exclude Title Field (Pos 19-79 for REV) from the check to allow words like "RESONANT"
                line_to_check = line
                if rec == "REV":
                    # Mask the title with spaces so we don't flag words inside it
                    line_to_check = line[:19] + (" " * 60) + line[79:]
                
                # Check for "NAN" surrounded by spaces or edges
                # This Regex looks for NAN as a whole word, not inside "RESONANT"
                if re.search(r'(?<!\w)NAN(?!\w)', line_to_check):
                    report.append({"level": "ERROR", "line": l_num, "message": "Syntax Fail: Standalone 'NAN' found in non-text field.", "content": line})

            if rec == "REV":
                # Vesna Position: ORI at 142
                if len(line) < 145 or line[142:145] != "ORI":
                    report.append({"level": "ERROR", "line": l_num, "message": "Alignment Fail: 'ORI' shifted from pos 142.", "content": line})

            if rec == "SWR":
                # Padding Check: IPI must start at 115
                ipi_val = line[115:126].strip()
                if not re.match(r'^\d{11}$', ipi_val):
                     # Only flag if it's not empty (empty IPIs are sometimes allowed, but Vesna prefers them padded)
                     if ipi_val != "":
                        report.append({"level": "ERROR", "line": l_num, "message": f"Padding Fail: IPI field malformed at pos 115.", "content": line})

            if rec == "SPT":
                # Vesna Share Rule
                if line[39:44] != "10000" or line[44:49] != "10000":
                    report.append({"level": "WARNING", "line": l_num, "message": "Compliance Alert: Admin Mechanical/Sync share is not 100%.", "content": line})

        return report, stats
