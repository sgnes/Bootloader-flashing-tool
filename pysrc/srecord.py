from . import srecutils

class Blocks(object):
    start_addr = None
    end_addr = None
    data = ""

class Srecords(object):

    def __init__(self, file_name):
        """

        """
        self.blocks = []
        with open(file_name) as sfile:
            blk = Blocks()
            for srec in sfile:
                srec = srec.strip("\n").strip("\r")
                record_type, data_len, addr, data, checksum = srecutils.parse_srec(srec)

                if record_type == 'S1' or record_type == 'S2' or record_type == 'S3':
                    addr_int = int(addr,16)
                    if blk.end_addr and addr_int > blk.end_addr:
                        self.blocks.append(blk)
                        blk = Blocks()
                    if not blk.start_addr:
                        blk.start_addr = addr_int
                    blk.data+=data
                    blk.end_addr = addr_int + (int(data_len,16) - 4)
                    raw_data = data
            self.blocks.append(blk)
            pass

    def get_data_by_addr(self, addr, size):
        """
        get the data by address and size;
        """
        data = None
        for blk in self.blocks:
            if blk.start_addr <= addr and blk.end_addr >= addr:
                #TODO: have to handle if the address cover more than two blocks
                data = blk.data[int((addr-blk.start_addr)*2):int((addr-blk.start_addr)*2) + 2*size]
        return data





