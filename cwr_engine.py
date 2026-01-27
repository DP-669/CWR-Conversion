import datetime
from mapping_config import PUBLISHER_MAPPING, SUB_PUB, SUBMITTER_INFO, WRITER_MAPPING

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
        """Converts '50' or '16.5' to CWR format '05000' or '01650'"""
        try:
            # Clean string
            s = str(share_val).replace('%', '')
            if not s or s.lower() == 'nan': return '00000'
            
            # Convert to float and multiply by 100 for CWR format (50.00 -> 5000)
            # But wait, CWR uses 3 decimal places implied? 
            # 'Dust Mites' 16.5% is shown as '01650' (which is 16.50)
            # '33%' is '03300' (33.00)
            # So we multiply by 100.
            val = float(s) * 100
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
        # Matching your big file GRH format exactly
        return f"GRHREV{self.pad(self.group_count, 5, 'right', '0')}02.200000000001"

    def generate_work_block(self, row):
        lines = []
        # Transaction ID: Increments per song (00000000, 00000001...)
        tid = self.pad(self.trans_count, 8, 'right', '0')
        self.trans_count += 1
        
        # 1. REV Record
        title = row.get('TRACK: Title', 'UNTITLED')
        iswc = self.pad(row.get('CODE: ISWC', ''), 11)
        # Using 'UNC' (Unconfirmed) and '000025Y' duration logic seen in big file
        rev = f"REV{tid}{self.pad(0, 8, 'right', '0')}{self.pad(title, 60)}{self.pad(row.get('TRACK: Number', ''), 14)}{iswc}0000000000            UNC000000Y      ORI                                                    00000000000                                                   Y"
        lines.append(rev)

        # LOOP: Process Writers & Publishers dynamically (Writer 1, 2, 3...)
        rec_seq = 1
        
        for i in range(1, 10): # Check up to 9 writers
            w_last = row.get(f'WRITER {i}: Last Name')
            if not w_last or str(w_last).lower() == 'nan': continue
            
            # Gather Writer Info
            w_first = row.get(f'WRITER {i}: First Name', '')
            w_ipi = self.pad(row.get(f'WRITER {i}: IPI', ''), 11, 'right', '0')
            op_name = row.get(f'WRITER {i}: Original Publisher', 'Redcola Publishing')
            
            # Shares logic (PR/MR/SR) from columns
            # In your big file: PR is split (16.5), MR/SR are full (33)
            pr_share = self.format_share(row.get(f'WRITER {i}: Owner Performance Share %', '0'))
            mr_share = self.format_share(row.get(f'WRITER {i}: Owner Mechanical Share %', '0'))
            
            # Lookup Publisher Data
            pub_data = PUBLISHER_MAPPING.get(op_name, {"agreement": "", "ipi": "00000000000", "internal_id": "000000000"})
            
            # --- SPU 1: Original Publisher ---
            # Note: Sequence ID (01, 02) logic depends on if we track distinct publishers. 
            # For simplicity in this engine, we pair 1 OP + 1 Sub per Writer.
            spu_op = f"SPU{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(i, 2, 'right', '0')}{self.pad(pub_data['internal_id'], 9)}{self.pad(op_name, 45)}E "
            spu_op += f"         {self.pad(pub_data['ipi'], 11, 'right', '0')}              021{pr_share}021{mr_share}   {mr_share} N                            {self.pad(pub_data['agreement'], 14)}PG"
            lines.append(spu_op)
            rec_seq += 1
            
            # --- SPU 2: Lumina (Sub) ---
            spu_sub = f"SPU{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(i, 2, 'right', '0')}{self.pad(SUB_PUB['internal_id'], 9)}{self.pad(SUB_PUB['name'], 45)}SE"
            spu_sub += f"         {self.pad(SUB_PUB['ipi'], 11, 'right', '0')}              052000000330000003300000 N                            {self.pad(pub_data['agreement'], 14)}PG"
            lines.append(spu_sub)
            rec_seq += 1
            
            # --- SPT: Territory ---
            # Hardcoded to UK (0826) as per your file
            spt = f"SPT{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(SUB_PUB['internal_id'], 9)}      {pr_share}{mr_share}{mr_share}I0826 001"
            lines.append(spt)
            rec_seq += 1
            
            # --- SWR: Writer ---
            swr = f"SWR{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(f'00000000{i}', 9)}{self.pad(w_last, 45)}{self.pad(w_first, 30)}C          {w_ipi}021{pr_share}990000009900000 N"
            lines.append(swr)
            rec_seq += 1
            
            # --- SWT: Writer Territory ---
            swt = f"SWT{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(f'00000000{i}', 9)}{pr_share}0000000000I2136 001"
            lines.append(swt)
            rec_seq += 1
            
            # --- PWR: Link ---
            pwr = f"PWR{tid}{self.pad(rec_seq, 8, 'right', '0')}{self.pad(pub_data['internal_id'], 9)}{self.pad(op_name, 45)}"
            pwr += f"                                       {self.pad(pub_data['agreement'], 14)}       {self.pad(f'00000000{i}', 9)}01"
            lines.append(pwr)
            rec_seq += 1

        self.record_count += len(lines)
        return "\n".join(lines)

    def make_trl(self):
        self.record_count += 2
        return f"GRT00001{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count - 1, 8, 'right', '0')}\nTRL00001{self.pad(self.trans_count, 8, 'right', '0')}{self.pad(self.record_count, 8, 'right', '0')}"
