import hid
import time
from datetime import datetime
from enum import IntEnum, auto

class CMD(IntEnum):
    BUF_RESET = 0
    BUF_SET_ADDR = auto()
    BUF_SET_DATA = auto()
    BUF_CHECKSUM = auto()
    PANEL_REFRESH = auto()
    SYS_RESTART = auto()
    SYS_BOOTLOADER = auto()
    NUM_COMMANDS = auto()

# TODO: classify so that dev doesn't need to be passed
def __send_cmd(dev, cmd, data=None):
    payload = [0, cmd]
    if data:
        payload.extend(data)
    return dev.write(payload)

def reset_buffer(dev):
    return __send_cmd(dev, CMD.BUF_RESET)

def set_addr(dev, addr):
    addr_split = [((addr >> 8*x) & 0xFF) for x in range(3)]
    print(f"setting addr: {addr} ({list(reversed(addr_split))})")
    return __send_cmd(dev, CMD.BUF_SET_ADDR, addr_split)

def write_data(dev, data):
    return __send_cmd(dev, CMD.BUF_SET_DATA, data)

try:
    print("Opening the device")

    h = hid.device()
    h.open(0xcafe, 0x4004)

    # enable non-blocking mode
    h.set_nonblocking(1)

    # write some data to the device
    # byte 0 always needs to be 0
    # b = b'\x00' + "Testing, 1,2,3".encode('utf-8')
    # h.write(b)
    start = datetime.now()
    num = 0

    # start here
    # split packet test 64 bytes at a time
    # 4096b: t: 0:00:01.025532 w/ no blocking print
    # 0:00:46.153676 for an entire image
    # for x in range(0, 2880):
    #     h.write([0] + [x%256] * 64)
    #     while True:
    #         d = h.read(64, 0.1)
    #         if d:
    #             num += 1
    #             print(f"{num} d[{len(d)}]: {d}")
    #         else:
    #             break

    # single packet test
    # NOTE: to do this, the entire data block needs to be built ahead of time
    # complete with the commands, len, etc!
    # 4096b: t: 0:00:00.523469 w/ no blocking print
    # 0:00:24.971527 for an entire image
    # however only 32 responses come back, and 8192b max
    # for x in range(0, 23):
    #     h.write([0] + [0] * 8192)
    #     while True:
    #         d = h.read(64, 0.1)
    #         if d:
    #             num += 1
    #             print(f"{num} d[{len(d)}]: {d}")
    #         else:
    #             break

    # reset buffer
    print("resetting buffer")
    # h.write([0, CMD.BUF_RESET])
    reset_buffer(h)

    # # write addr (LSB FIRST)
    # addr = 0
    # addr = [((addr >> 8*x) & 0xFF) for x in range(3)]
    # print(f"setting addr: {addr} ({addr})")
    # h.write([0, CMD.BUF_SET_ADDR] + addr)

    # # write some data
    # h.write([0, CMD.BUF_SET_DATA] + list(range(63)))

    # write addr (LSB FIRST)
    # addr = 8
    # addr = [((addr >> 8*x) & 0xFF) for x in range(3)]
    # print(f"setting addr: {addr} ({addr})")
    # h.write([0, CMD.BUF_SET_ADDR] + addr)
    set_addr(h, 8)

    # write some data
    # h.write([0, CMD.BUF_SET_DATA] + list(range(63, 80)))
    write_data(h, list(range(63, 80)))


    print(f"t: {datetime.now()-start}")

    print("Closing the device")
    h.close()

except IOError as ex:
    print(ex)

print("Done")
