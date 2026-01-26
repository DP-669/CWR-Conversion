import datetime
from mapping_config import PUBLISHER_MAPPING, SUB_PUB, SUBMITTER_INFO

class CWREngine:
    def __init__(self):
        self.trans_count = 0
        self.record_count = 0
        self.group_count = 0

    def pad(self, text, length, align='left', fill=' '):
        val = str(text).strip()
        if val.lower() in ['nan', 'none', '']: val = ""
        val = val.upper()[:length]
        return val.ljust(length, fill) if align == 'left' else val.rjust(length, fill)

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
        return f"GRH{self.pad('NWR', 3)}{self.pad(self.group_count, 5, 'right', '0')}{self.pad('02.10', 5)}{self.pad('', 10)}"

    def make_nwr_block(self, row):
        self.trans_count += 1
        lines = []
        
        title = row.get('TRACK: Title', 'UNTITLED')
        op_name = row.get('PUBLISHER 1: Name', 'Redcola Publishing')
        mapping = PUBLISHER_MAPPING.get(op_name, {"agreement": "0000000", "ipi": "00000000000"})
        
        # 1. NWR - Work Title
        lines.append(f"NWR{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(0, 8, 'right', '0')}{self.pad(title, 60)}{self.pad('', 14)}{self.pad(row.get('CODE: ISWC', ''), 11)}")
        
        # 2. SPU - Original Publisher (Role E)
        spu1 = f"SPU{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(1, 8, 'right', '0')}01{self.pad('', 9, '0')}{self.pad(op_name, 45)}E {self.pad('', 9)}{self.pad(mapping['ipi'], 11, 'right', '0')}"
        spu1 += f"050000500005000 N{self.pad(mapping['agreement'], 14)}PG"
        lines.append(spu1)
        
        # 3. SPU - Sub Publisher (Lumina - Role SE)
        spu2 = f"SPU{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(2, 8, 'right', '0')}01{self.pad('', 9, '0')}{self.pad(SUB_PUB['name'], 45)}SE{self.pad('', 9)}{self.pad(SUB_PUB['ipi'], 11, 'right', '0')}"
        spu2 += f"050000500005000 N{self.pad(mapping['agreement'], 14)}PG"
        lines.append(spu2)

        # 4. SPT - Territory for Sub-Publisher
        # Logic: 0826 is UK. Bible shows specific percentage logic for SPT.
        lines.append(f"SPT{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(3, 8, 'right', '0')}{self.pad(2, 8, '0')}{self.pad('', 6)}050001000010000I0826 001")

        # 5. Writers & PWR Link
        rec_id = 4
        writer_ipi = "00000000000"
        for i in range(1, 2): # Start with Writer 1 for linking
            last = row.get(f'WRITER {i}: Last Name')
            first = row.get(f'WRITER {i}: First Name')
            writer_ipi = self.pad(row.get(f'WRITER {i}: IPI', ''), 11, 'right', '0')
            
            if last and str(last).lower() != 'nan':
                # SWR
                lines.append(f"SWR{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(rec_id, 8, 'right', '0')}{self.pad(last, 45)}{self.pad(first, 30)}C {self.pad('', 9, '0')}{writer_ipi}021050000990000009900000 N")
                rec_id += 1
                # SWT - Writer Territory (2136 = World)
                lines.append(f"SWT{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(rec_id, 8, 'right', '0')}{self.pad(i, 3, 'right', '0')}050000000000000I2136 001")
                rec_id += 1
                # PWR - Link Writer to OP
                lines.append(f"PWR{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(rec_id, 8, 'right', '0')}{self.pad('', 9, '0')}{self.pad(op_name, 45)}{self.pad(mapping['agreement'], 14)}{self.pad(i, 3, 'right', '0')}01")
                rec_id += 1

        self.record_count += len(lines)
        return "\n".join(lines)

    def make_trl(self):
        self.record_count += 2
        return f"GRT00001{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count - 1, 8, 'right', '0')}\nTRL00001{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count, 8, 'right', '0')}"
