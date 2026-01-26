import datetime
from mapping_config import PUBLISHER_MAPPING, SUB_PUB, SUBMITTER_INFO

class CWREngine:
    def __init__(self):
        self.trans_count = 0
        self.record_count = 0
        self.group_count = 0

    def pad(self, text, length, align='left', fill=' '):
        """
        Forces exact character length. 
        Use fill='0' for IDs, fill=' ' for Text.
        """
        val = str(text).strip()
        if val.lower() == 'nan' or val == 'None':
            val = ""
        
        # Upper case for text, but keep numbers clean
        val = val.upper()
        
        # Truncate
        val = val[:length]
        
        if align == 'left':
            return val.ljust(length, fill)
        return val.rjust(length, fill)

    def get_role(self, role_str):
        # Maps CSV roles to CWR 2-char codes
        r = str(role_str).upper()
        if 'COMPOSER' in r and 'AUTHOR' in r: return 'CA'
        if 'COMPOSER' in r: return 'C '
        if 'AUTHOR' in r: return 'A '
        return 'CA' # Default

    def get_timestamp(self):
        now = datetime.datetime.now()
        return now.strftime("%Y%m%d"), now.strftime("%H%M%S")

    def make_hdr(self):
        d, t = self.get_timestamp()
        self.record_count += 1
        # HDR + SubmitterID(9) + Name(45) + Version(5) + Date(8) + Time(6) + Date(8)
        return f"HDR{self.pad(SUBMITTER_INFO['id'], 9, 'left', ' ')}{self.pad(SUBMITTER_INFO['name'], 45)}{self.pad('02.10', 5)}{d}{t}{d}"

    def make_grh(self):
        self.record_count += 1
        self.group_count += 1
        # GRH + Type(3) + GroupID(5) + Version(5)
        return f"GRH{self.pad('NWR', 3)}{self.pad(self.group_count, 5, 'right', '0')}{self.pad('02.10', 5)}{self.pad('', 10)}"

    def make_nwr_block(self, row):
        self.trans_count += 1
        lines = []
        
        # --- MAPPING & DATA PREP ---
        title = row.get('TRACK: Title', row.get('Work Title', 'UNTITLED'))
        op_name = row.get('PUBLISHER 1: Name', row.get('Original Publisher', 'Redcola Publishing'))
        
        # Get OP details
        mapping = PUBLISHER_MAPPING.get(op_name)
        if not mapping:
             # Fallback: Try finding partial match or default
             mapping = {"agreement": "0000000", "ipi": "00000000000"}

        # 1. NWR - Work Title
        # NWR + Trans(8-Zero) + Rec(8-Zero) + Title(60) + Lang(2) + Action(1) + ISWC(11)
        iswc = str(row.get('CODE: ISWC', '')).replace('.', '')
        if iswc.lower() == 'nan': iswc = ""
        
        nwr = f"NWR{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(0, 8, 'right', '0')}{self.pad(title, 60)}{self.pad('', 2)}{self.pad('', 1)}{self.pad(iswc, 11)}"
        lines.append(nwr)
        
        # 2. SPU - Original Publisher
        # SPU + Trans(8) + Rec(8) + Seq(2) + InternalID(9) + Name(45) + Role(2) + Soc(9) + IPI(11) ...
        # Note: The '01' is Sequence. '000000000' is the Internal ID slot found in Bible.
        spu1 = f"SPU{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(1, 8, 'right', '0')}01{self.pad('', 9, 'right', '0')}{self.pad(op_name, 45)}E {self.pad('', 9)}{self.pad(mapping['ipi'], 11, 'right', '0')}"
        
        # Add Shares (PR/MR/SR) - Assuming 50/100 split logic from Bible or CSV
        # Bible has: 10000 N (100.00%)
        # CSV has columns for shares, but for now we default to what usually works:
        spu1 += f"{self.pad('05000', 5, 'right', '0')}{self.pad('05000', 5, 'right', '0')}{self.pad('05000', 5, 'right', '0')} N"
        lines.append(spu1)
        
        # 3. SPU - Sub Publisher (Lumina)
        spu2 = f"SPU{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(2, 8, 'right', '0')}01{self.pad('', 9, 'right', '0')}{self.pad(SUB_PUB['name'], 45)}SE{self.pad('', 9)}{self.pad(SUB_PUB['ipi'], 11, 'right', '0')}"
        spu2 += f"{self.pad('05000', 5, 'right', '0')}{self.pad('05000', 5, 'right', '0')}{self.pad('05000', 5, 'right', '0')} N"
        lines.append(spu2)

        # 4. Writers Loop
        rec_id = 3
        for i in range(1, 4):
            last = row.get(f'WRITER {i}: Last Name')
            first = row.get(f'WRITER {i}: First Name')
            ipi = row.get(f'WRITER {i}: IPI')
            role = row.get(f'WRITER {i}: Capacity')
            
            if last and str(last).lower() != 'nan':
                cwr_role = self.get_role(role)
                
                # SWR + Trans(8) + Rec(8) + Last(45) + First(30) + Role(2) + InternalID(9) + IPI(11)
                swr = f"SWR{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(rec_id, 8, 'right', '0')}{self.pad(last, 45)}{self.pad(first, 30)}{cwr_role}{self.pad('', 9, 'right', '0')}{self.pad(ipi, 11, 'right', '0')}"
                swr += f"{self.pad('', 4)} N" # Soc info and PR share flag
                lines.append(swr)
                rec_id += 1

        self.record_count += len(lines)
        return "\n".join(lines)

    def make_trl(self):
        self.record_count += 2
        trl_block = f"GRT{self.pad(self.group_count, 5, 'right', '0')}{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count - 1, 8, 'right', '0')}\n"
        trl_block += f"TRL{self.pad(self.group_count, 5, 'right', '0')}{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count, 8, 'right', '0')}"
        return trl_block
