import re

class CWRValidator:
    def process_file(self, content):
        lines = content.split('\n')
        report = []
        
        for i, line in enumerate(lines):
            l_num = i + 1
            rec = line[0:3]
            
            # 1. Spacing Check (ORI at 142)
            if rec == "REV":
                if len(line) < 145 or line[142:145] != "ORI":
                    report.append(f"LINE {l_num}: Missing 'ORI' at position 142.")
            
            # 2. IPI Format Check (11 digits)
            if rec in ["SPU", "SWR", "HDR"]:
                ipi_pos = 87 if rec == "SPU" else (115 if rec == "SWR" else 3)
                len_ipi = 11
                ipi_val = line[ipi_pos:ipi_pos+len_ipi].strip()
                if not re.match(r'^\d{11}$', ipi_val):
                    report.append(f"LINE {l_num}: IPI '{ipi_val}' is not 11-digit zero-padded.")
            
            # 3. Admin Share Check (100% MR/SR)
            if rec == "SPT":
                mr = line[39:44]
                sr = line[44:49]
                if mr != "10000" or sr != "10000":
                    report.append(f"LINE {l_num}: Admin SPT must be 10000 (100%) for MR/SR.")

        return report
