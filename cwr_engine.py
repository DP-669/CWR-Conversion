import datetime
from mapping_config import PUBLISHER_MAPPING, SUB_PUB, SUBMITTER_INFO

class CWREngine:
    def __init__(self):
        self.trans_count = 0 
        self.record_count = 0
        self.group_count = 0

    def pad(self, text, length, align='left', fill=' '):
        val = str(text if text is not None and str(text).lower() != 'nan' else "").strip().upper()
        val = val.replace('.', '').replace('-', '') 
        return val.ljust(length, fill) if align == 'left' else val.rjust(length, fill)

    def format_share(self, share_val):
        """Converts percentage to 5-digit CWR format (16.5 -> 01650)"""
        try:
            val = float(str(share_val).replace('%', '')) * 100
            return f"{int(val):05d}"
        except:
            return '00000'

    def make_hdr(self):
        d = datetime.datetime.now().strftime("%Y%m%d")
        t = datetime.datetime.now().strftime("%H%M%S")
        self.record_count += 1
        return f"HDR{self.pad(SUBMITTER_INFO['id'], 9)}{self.pad(SUBMITTER_INFO['name'], 45)}01.10{d}{t}{d}               2.2001BACKBEAT"

    def make_grh(self):
        self.record_count += 1
        self.group_count += 1
        return f"GRHREV{self.pad(self.group_count, 5, 'right', '0')}02.200000000001"

    def generate_work_block(self, row):
        lines = []
        tid = self.pad(self.trans_count, 8, 'right', '0')
        self.trans_count += 1
        
        # 1. Main REV Record
        title = self.pad(row.get('TRACK: Title', 'UNTITLED'), 60)
        song_code = self.pad(row.get('CODE: Song Code', ''), 14)
        iswc = self.pad(row.get('CODE: ISWC', ''), 11)
        duration = self.pad(row.get('TRACK: Duration', '0'), 6, 'right', '0') + "Y"
        
        rev = f"REV{tid}{self.pad(0, 8, 'right', '0')}{title}{song_code}{iswc}0000000000            UNC{duration}      ORI                                                    00000000000                                                   Y"
        lines.append(rev)

        rec_seq = 1
        # Track active publishers for links
        pub_links = {}

        # 2. Publisher Loops (OP + Sub + Territory)
        for i in range(1, 4):
            op_name = str(row.get(f'PUBLISHER {i}: Name', '')).strip().upper()
            if not op_name or op_name == 'NAN': continue
            
            pub_data = PUBLISHER_MAPPING.get(op_name, {"agreement": "0000000", "ipi": "00000000000", "internal_id": "000000000"})
            pub_links[op_name] = pub_data['agreement']
            
            pr = self.format_share(row.get(f'PUBLISHER {i}: Owner Performance Share %', '0'))
            mr = self.format_share(row.get(f'PUBLISHER {i}: Owner Mechanical Share %', '0'))

            # SPU - Original Publisher
            lines.append(f"SPU{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(i, 2, 'right', '0')}{self.pad(pub_data['internal_id'], 9)}{self.pad(op_name, 45)}E          {self.pad(pub_data['ipi'], 11, 'right', '0')}              021{pr}021{mr}   {mr} N                            {self.pad(pub_data['agreement'], 14)}PG")
            rec_seq += 1
            # SPU - Lumina Sub-Pub
            lines.append(f"SPU{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(i, 2, 'right', '0')}{self.pad(SUB_PUB['internal_id'], 9)}{self.pad(SUB_PUB['name'], 45)}SE         {self.pad(SUB_PUB['ipi'], 11, 'right', '0')}              052000000{mr}00000{mr} N                            {self.pad(pub_data['agreement'], 14)}PG")
            rec_seq += 1
            # SPT - Territory (UK)
            lines.append(f"SPT{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(SUB_PUB['internal_id'], 9)}      {pr}{mr}{mr}I0826 001")
            rec_seq += 1

        # 3. Writer Loops (SWR + SWT + PWR)
        for i in range(1, 10):
            w_last = row.get(f'WRITER {i}: Last Name')
            if not w_last or str(w_last).lower() == 'nan': continue
            
            w_first = self.pad(row.get(f'WRITER {i}: First Name', ''), 30)
            w_ipi = self.pad(row.get(f'WRITER {i}: IPI', ''), 11, 'right', '0')
            pr = self.format_share(row.get(f'WRITER {i}: Owner Performance Share %', '0'))
            w_op = str(row.get(f'WRITER {i}: Original Publisher', '')).strip().upper()
            agree = pub_links.get(w_op, "0000000")

            # SWR
            lines.append(f"SWR{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(i, 9, 'right', '0')}{self.pad(w_last, 45)}{w_first}C          {w_ipi}021{pr}990000009900000 N")
            rec_seq += 1
            # SWT
            lines.append(f"SWT{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(i, 9, 'right', '0')}{pr}0000000000I2136 001")
            rec_seq += 1
            # PWR - Link to the OP
            lines.append(f"PWR{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad('000000000', 9)}{self.pad(w_op, 45)}                                       {self.pad(agree, 14)}       {self.pad(i, 9, 'right', '0')}01")
            rec_seq += 1

        # 4. Recording & Origin
        isrc = self.pad(row.get('CODE: ISRC', ''), 12)
        lines.append(f"REC{tid}{self.pad(rec_seq, 8, 'right', '0')}                        {song_code}                                                            {self.pad(row.get('ALBUM: Code', ''), 15)}{isrc}  CD                                                                                                                                                                                     RED COLA                                                    Y")
        rec_seq += 1
        lines.append(f"REC{tid}{self.pad(rec_seq, 8, 'right', '0')}                        000000                                                                                                                             {isrc}  DW {self.pad(row.get('TRACK: Title', ''), 60)}                                                                                                                                                                                                                                     Y")
        rec_seq += 1
        lines.append(f"ORN{tid}{self.pad(rec_seq, 8, 'right', '0')}LIB{self.pad(row.get('ALBUM: Title', ''), 45)}{self.pad(row.get('ALBUM: Code', ''), 15)}{self.pad(row.get('TRACK: Number', '1'), 4, 'right', '0')}RED COLA")

        self.record_count += len(lines)
        return "\n".join(lines)

    def make_trl(self):
        self.record_count += 2
        return f"GRT00001{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count - 1, 8, 'right', '0')}\nTRL00001{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count, 8, 'right', '0')}"
