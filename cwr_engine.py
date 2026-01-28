import datetime
from mapping_config import PUBLISHER_MAPPING, SUB_PUB, SUBMITTER_INFO, SOCIETY_MAP, WRITER_ID_MAP

class CWREngine:
    def __init__(self):
        self.trans_count = 0 
        self.record_count = 0
        self.group_count = 0
        self.auto_song_code = 1 

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

    def inject(self, grid, start, text):
        """Surgically inserts text into the character grid."""
        t_list = list(str(text))
        grid[start : start + len(t_list)] = t_list

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
        tid = self.pad(self.trans_count, 8, 'right', '0')
        self.trans_count += 1
        lines = []
        rec_seq = 0
        
        song_code = self.pad(self.auto_song_code, 7, 'right', '0')
        self.auto_song_code += 1

        title = row.get('TRACK: Title', 'UNTITLED').upper()
        iswc = self.pad(row.get('CODE: ISWC', ''), 11)
        duration = self.pad(row.get('TRACK: Duration', '0'), 6, 'right', '0')
        
        # 1. REV Record (260 chars)
        rev = [' '] * 260
        self.inject(rev, 0, "REV")
        self.inject(rev, 3, tid)
        self.inject(rev, 11, self.pad(rec_seq, 8, 'right', '0'))
        self.inject(rev, 19, title[:60])
        self.inject(rev, 81, song_code)
        self.inject(rev, 95, iswc)
        self.inject(rev, 106, "00000000")
        self.inject(rev, 126, "UNC")
        self.inject(rev, 129, duration)
        self.inject(rev, 135, "Y")
        self.inject(rev, 142, "ORI")
        self.inject(rev, 197, "00000000000")
        self.inject(rev, 259, "Y")
        lines.append("".join(rev))
        rec_seq += 1

        pub_links = {}
        for i in range(1, 4):
            op_name = str(row.get(f'PUBLISHER {i}: Name', '')).strip().upper()
            if not op_name or op_name == 'NAN': continue
            p_data = PUBLISHER_MAPPING.get(op_name, {"agreement": "0000000", "ipi": "00000000000", "internal_id": "000000000"})
            pub_links[op_name] = p_data
            pr = self.format_share(row.get(f'PUBLISHER {i}: Owner Performance Share %', '0'))
            mr = self.format_share(row.get(f'PUBLISHER {i}: Owner Mechanical Share %', '0'))

            spu1 = f"SPU{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(i, 2, 'right', '0')}{self.pad(p_data['internal_id'], 9)}{self.pad(op_name, 45)} E          {self.pad(p_data['ipi'], 11, 'right', '0')}              021{pr}021{mr}   {mr} N                            {self.pad(p_data['agreement'], 14)}PG"
            lines.append(spu1)
            rec_seq += 1
            spu2 = f"SPU{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(i, 2, 'right', '0')}{self.pad(SUB_PUB['internal_id'], 9)}{self.pad(SUB_PUB['name'], 45)} SE         {self.pad(SUB_PUB['ipi'], 11, 'right', '0')}              052000000{mr}00000{mr} N                            {self.pad(p_data['agreement'], 14)}PG"
            lines.append(spu2)
            rec_seq += 1
            lines.append(f"SPT{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(SUB_PUB['internal_id'], 9)}      {pr}{mr}{mr}I0826 001")
            rec_seq += 1

        for i in range(1, 4):
            w_last = str(row.get(f'WRITER {i}: Last Name', '')).strip().upper()
            if not w_last or w_last == 'NAN': continue
            w_id = WRITER_ID_MAP.get(w_last, f"00000000{i}")
            w_ipi = self.pad(row.get(f'WRITER {i}: IPI', ''), 11, 'right', '0')
            w_soc = SOCIETY_MAP.get(row.get(f'WRITER {i}: Society', ''), '021')
            w_pr = self.format_share(row.get(f'WRITER {i}: Owner Performance Share %', '0'))
            w_op = str(row.get(f'WRITER {i}: Original Publisher', '')).strip().upper()
            p_match = pub_links.get(w_op, {"agreement": "0000000", "internal_id": "000000000"})

            # 2. SWR Record (152 chars) - FIXES CRASH
            swr = [' '] * 152
            self.inject(swr, 0, "SWR")
            self.inject(swr, 3, tid)
            self.inject(swr, 11, self.pad(rec_seq, 8, 'right', '0'))
            self.inject(swr, 19, w_id)
            self.inject(swr, 28, self.pad(w_last, 45))
            self.inject(swr, 73, self.pad(row.get(f'WRITER {i}: First Name', ''), 30))
            self.inject(swr, 104, "C")
            self.inject(swr, 115, w_ipi)
            self.inject(swr, 126, f"{w_soc}{w_pr}")
            self.inject(swr, 134, "0990000009900000")
            self.inject(swr, 151, "N")
            lines.append("".join(swr))
            rec_seq += 1

            lines.append(f"SWT{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(w_id, 9)}{w_pr}0000000000I2136 001")
            rec_seq += 1
            
            pwr = [' '] * 112
            self.inject(pwr, 0, "PWR")
            self.inject(pwr, 3, tid)
            self.inject(pwr, 11, self.pad(rec_seq, 8, 'right', '0'))
            self.inject(pwr, 19, p_match.get('internal_id', '000000000'))
            self.inject(pwr, 28, self.pad(w_op, 45))
            self.inject(pwr, 87, self.pad(p_match.get('agreement', '0000000'), 14))
            self.inject(pwr, 101, self.pad(f"{w_id}{i:02d}", 11, 'right', '0'))
            lines.append("".join(pwr))
            rec_seq += 1

        isrc = self.pad(row.get('CODE: ISRC', ''), 12)
        album_code = self.pad(row.get('ALBUM: Code', ''), 15)
        # 3. REC Records (507 chars)
        for r_type in ["CD", "DW"]:
            rec = [' '] * 507
            self.inject(rec, 0, "REC")
            self.inject(rec, 3, tid)
            self.inject(rec, 11, self.pad(rec_seq, 8, 'right', '0'))
            self.inject(rec, 19, "00000000")
            self.inject(rec, 87, duration if r_type == "CD" else "000000")
            self.inject(rec, 90, song_code)
            self.inject(rec, 218, album_code)
            self.inject(rec, 249, isrc)
            self.inject(rec, 263, r_type)
            if r_type == "DW": self.inject(rec, 266, title[:60])
            if r_type == "CD": self.inject(rec, 446, "RED COLA")
            self.inject(rec, 506, "Y")
            lines.append("".join(rec))
            rec_seq += 1
        
        # 4. ORN Record (109 chars)
        orn = [' '] * 109
        self.inject(orn, 0, "ORN")
        self.inject(orn, 3, tid)
        self.inject(orn, 11, self.pad(rec_seq, 8, 'right', '0'))
        self.inject(orn, 19, "LIB")
        self.inject(orn, 22, self.pad(row.get('ALBUM: Title', ''), 45))
        self.inject(orn, 82, album_code)
        self.inject(orn, 97, self.pad(row.get('TRACK: Number', '1'), 4, 'right', '0'))
        self.inject(orn, 101, "RED COLA")
        lines.append("".join(orn))

        self.record_count += len(lines)
        return "\n".join(lines)

    def make_trl(self):
        self.record_count += 2
        return f"GRT00001{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count - 1, 8, 'right', '0')}\nTRL00001{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count, 8, 'right', '0')}"
