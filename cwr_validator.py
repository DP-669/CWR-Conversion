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

            if rec == "SWR": has_writer = True
            if rec == "SPU": has_publisher = True

            if rec == "REV":
                if len(line) < 145 or line[142:145] != "ORI":
                    report.append({"level": "ERROR", "line": l_num, "message": "Missing 'ORI' flag at position 142.", "content": line})
            
            if rec in ["SPU", "SWR"]:
                ipi_pos = 87 if rec == "SPU" else 115
                ipi_val = line[ipi_pos:ipi_pos+11].strip()
                if not re.match(r'^\d{11}$', ipi_val):
                    report.append({"level": "ERROR", "line": l_num, "message": f"Invalid IPI format: '{ipi_val}'.", "content": line})

            if rec == "SPT":
                if line[39:44] != "10000" or line[44:49] != "10000":
                    report.append({"level": "WARNING", "line": l_num, "message": "SPT Admin share is not 100%.", "content": line})

        return report, stats
