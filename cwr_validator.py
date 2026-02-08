import re

class CWRValidator:
    def process_file(self, content):
        lines = content.replace('\r\n', '\n').split('\n')
        report = []; stats = {"lines_read": len(lines), "transactions": 0}
        curr_work = None; has_w = False; has_p = False
        for i, line in enumerate(lines):
            l_num = i + 1
            if len(line) < 3: continue
            rec = line[0:3]
            if rec == "REV" or rec == "TRL":
                if curr_work:
                    if not has_w: report.append({"level": "CRITICAL", "line": l_num-1, "message": f"WORK '{curr_work}' HAS NO WRITERS.", "content": ""})
                    if not has_p: report.append({"level": "CRITICAL", "line": l_num-1, "message": f"WORK '{curr_work}' HAS NO PUBLISHERS.", "content": ""})
                if rec == "REV":
                    curr_work = line[19:79].strip(); has_w = False; has_p = False; stats["transactions"] += 1
            if rec == "SWR": has_w = True
            if rec == "SPU": has_p = True
            
            # Field-Aware NAN check: Mask titles to avoid false positives like "RESONANT"
            line_check = line
            if rec == "REV": line_check = line[:19] + (" " * 60) + line[79:]
            if re.search(r'(?<!\w)NAN(?!\w)', line_check):
                report.append({"level": "ERROR", "line": l_num, "message": "Syntax Fail: Standalone 'NAN' found in data field.", "content": line})
            
            if rec == "REV" and (len(line) < 145 or line[142:145] != "ORI"):
                report.append({"level": "ERROR", "line": l_num, "message": "Alignment Fail: 'ORI' shifted from pos 142.", "content": line})
            if rec == "SWR":
                ipi = line[115:126].strip()
                if ipi != "" and not re.match(r'^\d{11}$', ipi):
                    report.append({"level": "ERROR", "line": l_num, "message": "Padding Fail: IPI malformed at pos 115.", "content": line})
            if rec == "SPT" and (line[39:44] != "10000" or line[44:49] != "10000"):
                report.append({"level": "WARNING", "line": l_num, "message": "Compliance Alert: Admin Mechanical/Sync share is not 100%.", "content": line})
        return report, stats
