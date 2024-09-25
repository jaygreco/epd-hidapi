# Add root to path so modules in the parent directory are accessible
import os
import sys
here = os.path.dirname(os.path.abspath(__file__))
sys.path.append(here)

import logging
from datetime import datetime
from enum import IntEnum, auto

import hid
from csum import csum

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
    data_packed = [item for inner_list in data_split for item in [
        CMD.BUF_SET_DATA] + inner_list]
    return data_packed


class Panel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Panel init")
        self.dev = hid.device()
        self.dev.open(0xcafe, 0x4004)

    def __del__(self):
        self.logger.info("Panel deinit")
        self.dev.close()

    def __send_cmd(self, cmd, data=None):
        payload = [0] if cmd == CMD.NONE else [0, cmd]
        if data:
            payload.extend(data)
        return self.dev.write(payload)

    def reset_buffer(self):
        self.logger.info("Resetting buffer")
        return self.__send_cmd(CMD.BUF_RESET)

    def set_addr(self, addr):
        addr_split = [((addr >> 8*x) & 0xFF) for x in range(3)]
        self.logger.info(f"Setting addr: {addr} ({list(reversed(addr_split))})")
        return self.__send_cmd(CMD.BUF_SET_ADDR, addr_split)

    def write_data(self, data):
        self.logger.info(f"Writing data ({len(data)} bytes)")
        # The packed data already embeds CMD.BUF_SET_DATA, so use CMD.NONE
        # Chunk sends into 8kB, as >12kB is too big
        [self.__send_cmd(CMD.NONE, chunk)
         for chunk in chunks(pack_data(data), 8192)]

    def checksum(self, length):
        self.logger.info(f"Running checksum ({length} bytes)")
        length_split = [((length >> 8*x) & 0xFF) for x in range(3)]
        self.__send_cmd(CMD.BUF_CHECKSUM, length_split)
        res = self.dev.read(4)
        return (res[0] | res[1] << 8 | res[2] << 16 | res[3] << 24)

    def refresh(self):
        self.logger.info("Refreshing panel")
        return self.__send_cmd(CMD.PANEL_REFRESH)

    def restart_device(self):
        pass

    def enter_bootloader(self):
        pass

    # do it all, baby
    def upload_image(self, black_image, red_image):
        IMAGE_SIZE_MAX = 92160
        if len(black_image) > IMAGE_SIZE_MAX or len(black_image) > IMAGE_SIZE_MAX:
            self.logger.error(f"Image size exceeds max ({IMAGE_SIZE_MAX})!")
            return

        start = datetime.now()

        self.logger.info(f"Uploading image to panel")
        # reset buffer
        self.reset_buffer()

        # write image data (black)
        self.write_data(black_image)

        # checksum (black)
        self.set_addr(0)
        dev_checksum = self.checksum(len(black_image))
        local_checksum = csum(black_image)
        self.logger.info(f"Device checksum: {hex(dev_checksum)}")
        self.logger.info(f"Local checksum: {hex(local_checksum)}")
        if dev_checksum == local_checksum:
            self.logger.info("Black checksum ok")
        else:
            self.logger.info("BLACK CHECKSUM MISMATCH!")

        # write image data (red)
        self.set_addr(len(black_image))
        self.write_data(red_image)

        # checksum (red)
        self.set_addr(len(red_image))
        dev_checksum = self.checksum(len(red_image))
        local_checksum = csum(red_image)
        self.logger.info(f"Device checksum: {hex(dev_checksum)}")
        self.logger.info(f"Local checksum: {hex(local_checksum)}")
        if dev_checksum == local_checksum:
            self.logger.info("Red checksum ok")
        else:
            self.logger.info("RED CHECKSUM MISMATCH!")

        # refresh
        self.refresh()

        self.logger.info(f"Done. Process took {datetime.now()-start}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create a test patten to display
    red_image = [0x00]*46080 + [0xFF]*46080
    black_image = [0xFF]*46080 + [0x00]*46080

    panel = Panel()
    panel.upload_image(black_image, red_image)
