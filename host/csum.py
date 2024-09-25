
# shift <stride> num of elements into a single integer
def __shift_and_stack(l, stride):
    # pad l to stride width
    while len(l) < stride:
        l.extend([0x0])

    result = 0
    [result := (result | l[-(x+1)] << (8*x)) for x in range(stride)]
    return result


def csum(l):
    # NOTE: can seed the checksum with a starting value
    checksum = 0
    STRIDE = 4
    [checksum := (__shift_and_stack(l[x:x+STRIDE], STRIDE) ^ checksum)
     for x in range(0, len(l), STRIDE)]
    return checksum


if __name__ == "__main__":
    l = [0x9A, 0xCE, 0xB1, 0x1A, 0x00, 0x21, 0x89, 0x23, 0x69, 0x45]
    print(f"l: {hex(csum(l))}")
