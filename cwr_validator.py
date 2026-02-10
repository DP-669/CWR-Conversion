import re

class CWRValidator:
    def process_file(self, content):
        # Normalize line endings
        lines = content.replace('\r\n', '\n').split('\n')
        report = []
        stats = {"lines_read": len(lines), "transactions": 0}
        
        curr_work = None
        has_w = False
        has_p = False
        
        # Valid Transaction Start Tags
        TRANS_TAGS = ["REV", "NWR"]

        for i, line in enumerate(lines):
            l_num = i + 1
            if len(line) < 3: continue
            
            rec = line[0:3]
            
            # 1. LOGIC CHECKS (End of previous transaction)
            # If we hit a new transaction OR the trailer, check the previous work
            if rec in TRANS_TAGS or rec == "GRT" or rec == "TRL":
                if curr_work:
                    if not has_w:
                        report.append({
                            "level": "CRITICAL", 
                            "line": l_num-1, 
                            "message": f"WORK '{curr_work}' HAS NO WRITERS.", 
                            "content": ""
                        })
                    if not has_p:
                        report.append({
                            "level": "CRITICAL", 
                            "line": l_num-1, 
                            "message": f"WORK '{curr_work}' HAS NO PUBLISHERS.", 
                            "content": ""
                        })
                
                # If this line is a new transaction, reset state
                if rec in TRANS_TAGS:
                    # Title is at 19:79 for both REV and NWR
                    curr_work = line[19:79].strip() 
                    has_w = False
                    has_p = False
                    stats["transactions"] += 1
            
            # 2. COMPONENT CHECKS
            if rec == "SWR": has_w = True
            if rec == "SPU": has_p = True
            
            # 3. SYNTAX & GEOMETRY CHECKS
            
            # A. Field-Aware NAN check
            # Mask the Title field (19-79) to prevent false positives like "BANANA" or "RESONANT"
            line_check = line
            if rec in TRANS_TAGS:
                line_check = line[:19] + (" " * 60) + line[79:]
            
            # Regex: look for NAN surrounded by boundaries, excluding the masked title
            if re.search(r'(?<!\w)NAN(?!\w)', line_check):
                report.append({
                    "level": "ERROR", 
                    "line": l_num, 
                    "message": "Syntax Fail: Standalone 'NAN' found in data field.", 
                    "content": line
                })
            
            # B. Anchor Point Check (ORI)
            # Both REV and NWR must have "ORI" at 142
            if rec in TRANS_TAGS:
                if len(line) < 145 or line[142:145] != "ORI":
                    report.append({
                        "level": "ERROR", 
                        "line": l_num, 
                        "message": f"Alignment Fail: '{rec}' record missing 'ORI' at pos 142.", 
                        "content": line
                    })
            
            # C. IPI Padding Check
            if rec == "SWR":
                ipi = line[115:126].strip()
                # If IPI exists, it must be 11 digits (all numbers)
                if ipi != "" and not re.match(r'^\d{11}$', ipi):
                    report.append({
                        "level": "ERROR", 
                        "line": l_num, 
                        "message": f"Padding Fail: IPI '{ipi}' is not 11 digits.", 
                        "content": line
                    })

        return report, stats
