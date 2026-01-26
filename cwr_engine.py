import datetime
from mapping_config import PUBLISHER_MAPPING, SUB_PUB, SUBMITTER_INFO

class CWREngine:
    def __init__(self):
        self.trans_count = 0
        self.record_count = 0
        self.group_count = 0

    def pad(self, text, length, align='left', fill=' '):
        val = str(text if text is not None and str(text).lower() != 'nan' else "").strip().upper()
        val = val[:length]
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
        iswc = str(row.get('CODE: ISWC', '')).replace('.', '')
        if iswc.lower() == 'nan': iswc = ""
        
        # 1. NWR
        # Fixed Spacing: NWR + Trans(8) + Rec(8) + Title(60) + Lang(2) + Action(1) + ISWC(11)
        nwr = f"NWR{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(0, 8, 'right', '0')}"
        nwr += f"{self.pad(title, 60)}{self.pad('', 14)}{self.pad(iswc, 11)}"
        lines.append(nwr)
        
        # 2. SPU - Original Publisher (Role E)
        spu1 = f"SPU{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(1, 8, 'right', '0')}01{self.pad('', 9)}{self.pad(op_name, 45)}E "
        spu1 += f"{self.pad('', 9)}{self.pad(mapping['ipi'], 11, 'right', '0')}0210500002110000   10000 N{self.pad('', 27)}{self.pad(mapping['agreement'], 14)}PG"
        lines.append(spu1)
        
        # 3. SPU - Sub Publisher (Lumina - Role SE)
        spu2 = f"SPU{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(2, 8, 'right', '0')}01{self.pad('', 9)}{self.pad(SUB_PUB['name'], 45)}SE"
        spu2 += f"{self.pad('', 9)}{self.pad(SUB_PUB['ipi'], 11, 'right', '0')}052000000330000003300000 N{self.pad('', 27)}{self.pad(mapping['agreement'], 14)}PG"
        lines.append(spu2)

        # 4. SPT - Territory for Sub-Publisher (Aligning Sequence number with Bible)
        # Bible uses position 25-32 as '00000012' for this record.
        lines.append(f"SPT{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(3, 8, 'right', '0')}{self.pad('00000012', 8, 'right', '0')}{self.pad('', 6)}050001000010000I0826 001")

        # 5. Writers & PWR Link
        rec_id = 4
        writer_ipi = self.pad(row.get('WRITER 1: IPI', ''), 11, 'right', '0')
        writer_last = row.get('WRITER 1: Last Name', '')
        writer_first = row.get('WRITER 1: First Name', '')
            
        # SWR
        swr = f"SWR{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(rec_id, 8, 'right', '0')}{self.pad('000000107', 9, 'right', '0')}"
        swr = f"SWR{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(rec_id, 8, 'right', '0')}{self.pad(writer_last, 45)}{self.pad(writer_first, 30)}C "
        swr += f"{self.pad('', 9)}{writer_ipi}021050000990000009900000 N"
        lines.append(swr)
        rec_id += 1
        
        # SWT
        lines.append(f"SWT{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(rec_id, 8, 'right', '0')}{self.pad('001', 3, 'right', '0')}{self.pad('', 12)}050000000000000I2136 001")
        rec_id += 1
        
        # PWR - Link
        pwr = f"PWR{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(rec_id, 8, 'right', '0')}{self.pad('', 9)}{self.pad(op_name, 45)}"
        pwr += f"{self.pad('', 39)}{self.pad(mapping['agreement'], 14)}{self.pad('001', 3, 'right', '0')}01"
        lines.append(pwr)

        self.record_count += len(lines)
        return "\n".join(lines)

    def make_trl(self):
        self.record_count += 2
        trl = f"GRT00001{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count - 1, 8, 'right', '0')}\n"
        trl += f"TRL00001{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count, 8, 'right', '0')}"
        return trl
