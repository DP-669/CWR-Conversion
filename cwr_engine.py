# cwr_engine.py
import datetime
from mapping_config import PUBLISHER_MAPPING, SUB_PUB, SUBMITTER_INFO

class CWREngine:
    def __init__(self):
        self.trans_count = 0
        self.record_count = 0
        self.group_count = 0

    def pad(self, text, length, align='left'):
        """Forces exact character length with space padding."""
        text = str(text if text is not None else "").upper()[:length]
        return text.ljust(length) if align == 'left' else text.rjust(length)

    def get_timestamp(self):
        now = datetime.datetime.now()
        return now.strftime("%Y%m%d"), now.strftime("%H%M%S")

    def make_hdr(self):
        d, t = self.get_timestamp()
        self.record_count += 1
        # Format: Type(3) + SubmitterID(9) + Name(45) + Version(5) + Date(8) + Time(6)
        return f"HDR{self.pad(SUBMITTER_INFO['id'], 9)}{self.pad(SUBMITTER_INFO['name'], 45)}{self.pad('02.10', 5)}{d}{t}{d}"

    def make_grh(self):
        self.record_count += 1
        self.group_count += 1
        # Group Header for New Work Registrations (NWR)
        return f"GRH{self.pad('NWR', 3)}{self.pad(self.group_count, 5, 'right')}{self.pad('02.10', 5)}{self.pad('', 10)}"

    def make_nwr_block(self, row):
        """Processes one CSV row into a CWR work block."""
        self.trans_count += 1
        lines = []
        op_name = row.get('Original Publisher', 'Redcola Publishing')
        mapping = PUBLISHER_MAPPING.get(op_name, {"agreement": "0000000", "ipi": "00000000000"})
        
        # NWR - The Work
        nwr = f"NWR{self.pad(self.trans_count, 8, 'right')}{self.pad(0, 8, 'right')}{self.pad(row['Work Title'], 60)}"
        lines.append(nwr)
        
        # SPU - Original Publisher
        spu1 = f"SPU{self.pad(self.trans_count, 8, 'right')}{self.pad(1, 8, 'right')}01{self.pad(op_name, 45)}E{self.pad(mapping['ipi'], 11)}"
        lines.append(spu1)
        
        # SPU - Sub Publisher (Lumina)
        spu2 = f"SPU{self.pad(self.trans_count, 8, 'right')}{self.pad(2, 8, 'right')}01{self.pad(SUB_PUB['name'], 45)}SE{self.pad(SUB_PUB['ipi'], 11)}"
        lines.append(spu2)

        # SWR - Writer (Using Damir logic: CA role)
        swr = f"SWR{self.pad(self.trans_count, 8, 'right')}{self.pad(3, 8, 'right')}{self.pad(row.get('Writer 1 Last Name', ''), 45)}CA{self.pad(row.get('Writer 1 IPI', ''), 11)}"
        lines.append(swr)

        self.record_count += len(lines)
        return "\n".join(lines)

    def make_trl(self):
        self.record_count += 2 # For GRT and TRL
        trl_block = f"GRT{self.pad(self.group_count, 5, 'right')}{self.pad(self.trans_count, 8, 'right')}{self.pad(self.record_count - 1, 8, 'right')}\n"
        trl_block += f"TRL{self.pad(self.group_count, 5, 'right')}{self.pad(self.trans_count, 8, 'right')}{self.pad(self.record_count, 8, 'right')}"
        return trl_block