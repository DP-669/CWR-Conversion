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

            # --- TRANSITION LOGIC ---
            if rec == "REV" or rec == "TRL":
                # Audit previous work before starting new one
                if current_work:
                    if not has_writer:
                        report.append({"level": "CRITICAL", "line": l_num-1, "message": f"WORK '{current_work}' HAS NO WRITERS. Rejecting.", "content": ""})
                    if not has_publisher:
                        report.append({"level": "CRITICAL", "line": l_num-1, "message": f"WORK '{current_work}' HAS NO PUBLISHERS. Rejecting.", "content": ""})
                
                if rec == "REV":
                    current_work = line[19:79].strip()
                    has_writer = False
                    has_publisher = False
                    stats["transactions"] += 1

            # --- DATA AUDIT ---
            if rec == "SWR": has_writer = True
            if rec == "SPU": has_publisher = True

            # --- SYNTAX CHECKS ---
            if rec == "REV":
                # Spacing (ORI at 142)
                if len(line) < 145 or line[142:145] != "ORI":
                    report.append({"level": "ERROR", "line": l_num, "message": "Missing 'ORI' flag at position 142.", "content": line})
            
            if rec in ["SPU", "SWR"]:
                # IPI Format (11 digits)
                ipi_pos = 87 if rec == "SPU" else 115
                ipi_val = line[ipi_pos:ipi_pos+11].strip()
                if not re.match(r'^\d{11}$', ipi_val):
                    report.append({"level": "ERROR", "line": l_num, "message": f"Invalid IPI format: '{ipi_val}'. Must be 11 digits.", "content": line})

            if rec == "SPT":
                # Admin Collection Rule
                if line[39:44] != "10000" or line[44:49] != "10000":
                    # Only check if it's the Lumina Admin record (identified by previous SPU SE)
                    # For safety, we warn if any SPT is not 100% since that's your UK rule
                    report.append({"level": "WARNING", "line": l_num, "message": "SPT Share is not 100%. Verify if this is intended.", "content": line})

        return report, stats
