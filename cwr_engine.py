# cwr_engine.py
import datetime
from mapping_config import PUBLISHER_MAPPING, SUB_PUB, SUBMITTER_INFO

class CWREngine:
    def __init__(self):
        self.trans_count = 0
        self.record_count = 0
        self.group_count = 0

    def pad(self, text, length, align='left'):
        val = str(text if text is not None and str(text).lower() != 'nan' else "").upper()[:length]
        return val.ljust(length) if align == 'left' else val.rjust(length)

    def get_timestamp(self):
        now = datetime.datetime.now()
        return now.strftime("%Y%m%d"), now.strftime("%H%M%S")

    def make_hdr(self):
        d, t = self.get_timestamp()
        self.record_count += 1
        return f"HDR{self.pad(SUBMITTER_INFO['id'], 9)}{self.pad(SUBMITTER_INFO['name'], 45)}{self.pad('02.10', 5)}{d}{t}{d}"

    def make_grh(self):
        self.record_count += 1
        self.group_count += 1
        return f"GRH{self.pad('NWR', 3)}{self.pad(self.group_count, 5, 'right')}{self.pad('02.10', 5)}{self.pad('', 10)}"

    def make_nwr_block(self, row):
        self.trans_count += 1
        lines = []
        
        # Column Name Mapping (Handling the 'Bible' CSV prefixes)
        title = row.get('TRACK: Title', row.get('Work Title', 'UNTITLED'))
        op_name = row.get('PUBLISHER 1: Name', row.get('Original Publisher', 'Redcola Publishing'))
        mapping = PUBLISHER_MAPPING.get(op_name, {"agreement": "0000000", "ipi": "00000000000"})
        
        # 1. NWR - Work Title
        nwr = f"NWR{self.pad(self.trans_count, 8, 'right')}{self.pad(0, 8, 'right')}{self.pad(title, 60)}"
        lines.append(nwr)
        
        # 2. SPU - Original Publisher
        spu1 = f"SPU{self.pad(self.trans_count, 8, 'right')}{self.pad(1, 8, 'right')}01{self.pad(op_name, 45)}E{self.pad(mapping['ipi'], 11)}"
        lines.append(spu1)
        
        # 3. SPU - Sub Publisher (Lumina)
        spu2 = f"SPU{self.pad(self.trans_count, 8, 'right')}{self.pad(2, 8, 'right')}01{self.pad(SUB_PUB['name'], 45)}SE{self.pad(SUB_PUB['ipi'], 11)}"
        lines.append(spu2)

        # 4. Writers Loop (Handles up to 3 writers if they exist in CSV)
        rec_id = 3
        for i in range(1, 4):
            last_name = row.get(f'WRITER {i}: Last Name')
            ipi = row.get(f'WRITER {i}: IPI')
            if last_name and str(last_name).lower() != 'nan':
                swr = f"SWR{self.pad(self.trans_count, 8, 'right')}{self.pad(rec_id, 8, 'right')}{self.pad(last_name, 45)}CA{self.pad(ipi, 11)}"
                lines.append(swr)
                rec_id += 1

        self.record_count += len(lines)
        return "\n".join(lines)

    def make_trl(self):
        self.record_count += 2
        trl_block = f"GRT{self.pad(self.group_count, 5, 'right')}{self.pad(self.trans_count, 8, 'right')}{self.pad(self.record_count - 1, 8, 'right')}\n"
        trl_block += f"TRL{self.pad(self.group_count, 5, 'right')}{self.pad(self.trans_count, 8, 'right')}{self.pad(self.record_count, 8, 'right')}"
        return trl_block
