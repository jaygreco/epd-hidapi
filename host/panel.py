from csum import csum
from datetime import datetime
from enum import IntEnum, auto
import hid
from image import extract_image
import time

class CMD(IntEnum):
    BUF_RESET = 0
    BUF_SET_ADDR = auto()
    BUF_SET_DATA = auto()
    BUF_CHECKSUM = auto()
    PANEL_REFRESH = auto()
    SYS_RESTART = auto()
    SYS_BOOTLOADER = auto()
    NONE = auto()

def chunks(xs, n):
    n = max(1, n)
    return [xs[i:i+n] for i in range(0, len(xs), n)]

def pack_data(data):
    # Split data into 63-byte chunks 
    CHUNK_SIZE = 63
    data_split = chunks(data, CHUNK_SIZE)
    # Prepend a CMD.BUF_SET_DATA before each packet
    data_packed = [item for inner_list in data_split for item in [CMD.BUF_SET_DATA] + inner_list]
    return data_packed

class Panel:
    def __init__(self):
        print("panel init")
        self.dev = hid.device()
        self.dev.open(0xcafe, 0x4004)

    def __del__(self):
        print("panel deinit")
        self.dev.close()

    def __send_cmd(self, cmd, data=None):
        payload = [0] if cmd == CMD.NONE else [0, cmd]
        if data:
            payload.extend(data)
        return self.dev.write(payload)

    def reset_buffer(self):
        print("resetting buffer")
        return self.__send_cmd(CMD.BUF_RESET)

    def set_addr(self, addr):
        addr_split = [((addr >> 8*x) & 0xFF) for x in range(3)]
        print(f"setting addr: {addr} ({list(reversed(addr_split))})")
        return self.__send_cmd(CMD.BUF_SET_ADDR, addr_split)

    def write_data(self, data):
        print(f"writing data ({len(data)} bytes)")
        # The packed data already embeds CMD.BUF_SET_DATA, so use CMD.NONE
        # Chunk sends into 8kB, as >12kB is too big
        [self.__send_cmd(CMD.NONE, chunk) for chunk in chunks(pack_data(data), 8192)]

    def checksum(self, length):
        print(f"running checksum ({length} bytes)")
        length_split = [((length >> 8*x) & 0xFF) for x in range(3)]
        self.__send_cmd(CMD.BUF_CHECKSUM, length_split)
        res = self.dev.read(4)
        return (res[0] | res[1] << 8 | res[2] << 16 | res[3] << 24)

    def refresh(self):
        print("refreshing panel")
        return self.__send_cmd(CMD.PANEL_REFRESH)

    def restart_device(self):
        pass

    def enter_bootloader(self):
        pass

    # do it all, baby
    def upload_image(self, image):
        print(f"uploading image to panel: {image}")
        # reset buffer
        self.reset_buffer()

        # write image data (black)
        black_image, red_image = extract_image(image, rotation=90)
        self.write_data(black_image)

        # checksum (black)
        self.set_addr(0)
        dev_checksum = self.checksum(len(black_image))
        local_checksum = csum(black_image)
        print(f"device checksum: {hex(dev_checksum)}")
        print(f"local checksum: {hex(local_checksum)}")
        if dev_checksum == local_checksum:
            print("black checksum ok")
        else:
            print("BLACK CHECKSUM MISMATCH!")

        # write image data (red)
        self.set_addr(len(black_image))
        self.write_data(red_image)

        # checksum (red)
        self.set_addr(len(red_image))
        dev_checksum = self.checksum(len(red_image))
        local_checksum = csum(red_image)
        print(f"device checksum: {hex(dev_checksum)}")
        print(f"local checksum: {hex(local_checksum)}")
        if dev_checksum == local_checksum:
            print("red checksum ok")
        else:
            print("RED CHECKSUM MISMATCH!")

        # refresh
        self.refresh()


if __name__ == "__main__":
    start = datetime.now()

    panel = Panel()
    panel.upload_image("test.bmp")

    print(f"t: {datetime.now()-start}")
    print("Done")
