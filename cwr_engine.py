import datetime
from mapping_config import PUBLISHER_MAPPING, SUB_PUB, SUBMITTER_INFO, SOCIETY_MAP, WRITER_ID_MAP

class CWREngine:
    def __init__(self):
        self.trans_count = 0 
        self.record_count = 0
        self.group_count = 0

    def pad(self, text, length, align='left', fill=' '):
        val = str(text if text is not None and str(text).lower() != 'nan' else "").strip().upper()
        val = val.replace('.', '').replace('-', '') 
        val = val[:length]
        return val.ljust(length, fill) if align == 'left' else val.rjust(length, fill)

    def format_share(self, share_val):
        try:
            val = float(str(share_val).replace('%', '')) * 100
            return f"{int(val):05d}"
        except: return '00000'

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
        # Transaction ID stays constant for the entire block
        tid = self.pad(self.trans_count, 8, 'right', '0')
        self.trans_count += 1
        
        lines = []
        rec_seq = 0
        
        # 1. REV Record (Precisely mapped indices)
        title = self.pad(row.get('TRACK: Title', 'UNTITLED'), 60)
        song_code = self.pad(row.get('CODE: Song Code', ''), 7, 'right', '0')
        iswc = self.pad(row.get('CODE: ISWC', ''), 11)
        duration = self.pad(row.get('TRACK: Duration', '0'), 6, 'right', '0')
        
        rev = list(self.pad("", 260))
        rev[0:3] = "REV"
        rev[3:11] = tid
        rev[11:19] = self.pad(rec_seq, 8, 'right', '0')
        rev[19:79] = list(title)
        rev[81:88] = list(song_code)
        rev[95:106] = list(iswc)
        rev[106:114] = list("00000000")
        rev[126:129] = list("UNC")
        rev[129:135] = list(duration)
        rev[135] = "Y"
        rev[142:145] = list("ORI")
        rev[197:208] = list("00000000000")
        rev[259] = "Y"
        lines.append("".join(rev))
        rec_seq += 1

        pub_links = {}
        # Multi-Publisher loop (SPU + SPT)
        for i in range(1, 4):
            op_name = str(row.get(f'PUBLISHER {i}: Name', '')).strip().upper()
            if not op_name or op_name == 'NAN': continue
            
            p_data = PUBLISHER_MAPPING.get(op_name, {"agreement": "0000000", "ipi": "00000000000", "internal_id": "000000000"})
            pub_links[op_name] = p_data['agreement']
            pr = self.format_share(row.get(f'PUBLISHER {i}: Owner Performance Share %', '0'))
            mr = self.format_share(row.get(f'PUBLISHER {i}: Owner Mechanical Share %', '0'))

            # SPU - OP
            spu1 = f"SPU{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(i, 2, 'right', '0')}{self.pad(p_data['internal_id'], 9)}{self.pad(op_name, 45)} E          {self.pad(p_data['ipi'], 11, 'right', '0')}              021{pr}021{mr}   {mr} N                            {self.pad(p_data['agreement'], 14)}PG"
            lines.append(spu1)
            rec_seq += 1
            # SPU - SUB
            spu2 = f"SPU{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(i, 2, 'right', '0')}{self.pad(SUB_PUB['internal_id'], 9)}{self.pad(SUB_PUB['name'], 45)} SE         {self.pad(SUB_PUB['ipi'], 11, 'right', '0')}              052000000{mr}00000{mr} N                            {self.pad(p_data['agreement'], 14)}PG"
            lines.append(spu2)
            rec_seq += 1
            # SPT
            lines.append(f"SPT{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(SUB_PUB['internal_id'], 9)}      {pr}{mr}{mr}I0826 001")
            rec_seq += 1

        # Multi-Writer loop
        for i in range(1, 4):
            w_last = str(row.get(f'WRITER {i}: Last Name', '')).strip().upper()
            if not w_last or w_last == 'NAN': continue
            
            w_id = WRITER_ID_MAP.get(w_last, f"00000000{i}")
            w_ipi = self.pad(row.get(f'WRITER {i}: IPI', ''), 11, 'right', '0')
            w_soc = SOCIETY_MAP.get(row.get(f'WRITER {i}: Society', ''), '021')
            w_pr = self.format_share(row.get(f'WRITER {i}: Owner Performance Share %', '0'))
            w_op = str(row.get(f'WRITER {i}: Original Publisher', '')).strip().upper()
            agree = pub_links.get(w_op, "0000000")

            lines.append(f"SWR{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(w_id, 9)}{self.pad(w_last, 45)}{self.pad(row.get(f'WRITER {i}: First Name', ''), 30)} C          {w_ipi}{w_soc}{w_pr}0990000009900000 N")
            rec_seq += 1
            lines.append(f"SWT{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(w_id, 9)}{w_pr}0000000000I2136 001")
            rec_seq += 1
            lines.append(f"PWR{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad('000000000', 9)}{self.pad(w_op, 45)}                                       {self.pad(agree, 14)}       {self.pad(w_id, 9, 'right', '0')}01")
            rec_seq += 1

        # REC Records
        isrc = self.pad(row.get('CODE: ISRC', ''), 12)
        album_code = self.pad(row.get('ALBUM: Code', ''), 15)
        
        # REC 01 (Digital Work)
        rec1 = list(self.pad("", 507))
        rec1[0:3] = "REC"
        rec1[3:11] = tid
        rec1[11:19] = self.pad(rec_seq, 8, 'right', '0')
        rec1[19:27] = list("00000000")
        rec1[87:93] = list(duration)
        rec1[218:233] = list(" " + album_code[:-1])
        rec1[249:261] = list(" " + isrc[:-1])
        rec1[263:265] = list("CD")
        rec1[446:454] = list("RED COLA")
        rec1[506] = "Y"
        lines.append("".join(rec1))
        rec_seq += 1

        # REC 02
        rec2 = list(self.pad("", 507))
        rec2[0:3] = "REC"
        rec2[3:11] = tid
        rec2[11:19] = self.pad(rec_seq, 8, 'right', '0')
        rec2[87:93] = list("000000")
        rec2[249:261] = list(" " + isrc[:-1])
        rec2[263:265] = list("DW")
        rec2[266:266+len(title[:60])] = list(title[:60])
        rec2[506] = "Y"
        lines.append("".join(rec2))
        rec_seq += 1
        
        # ORN Record
        album_title = self.pad(row.get('ALBUM: Title', ''), 45)
        track_num = self.pad(row.get('TRACK: Number', '1'), 4, 'right', '0')
        orn = f"ORN{tid}{self.pad(rec_seq, 8, 'right', '0')}LIB{album_title}{self.pad(album_code, 15)}{track_num}RED COLA"
        lines.append(orn)

        self.record_count += len(lines)
        return "\n".join(lines)

    def make_trl(self):
        self.record_count += 2
        return f"GRT00001{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count - 1, 8, 'right', '0')}\nTRL00001{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count, 8, 'right', '0')}"
