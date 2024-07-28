from enum import IntEnum
from PIL import Image

def extract_image(image_path, threshold=128, rotation=0):
    print("extracting red/black pixels from image")

    class COLOR(IntEnum):
        R = 0
        G = 1
        B = 2

    img = Image.open(image_path).convert('RGB')
    img = img.rotate(rotation, expand=True)
    width, height = img.size
    pixels = img.load()
    
    # Prepare an empty list for the byte-packed binary data
    bit_array_black = []
    byte_black = 0
    bit_array_red = []
    byte_red = 0
    bit_count = 0
    
    for y in range(height):
        for x in range(width):
            pixel_value = pixels[x, y]

            # To extract black pixels, use the red channel, since pure black pixels
            # also have a red component
            bit = 1 if pixel_value[COLOR.R] >= threshold else 0

            # Invert the bit and pack into the byte
            byte_black = (byte_black << 1) | (1 - bit)

            # To extract red pixels, we can XOR the blue channel with the red channel.
            # Pixels that don't show up in both are pure red
            bit_r = 1 if pixel_value[COLOR.R] >= threshold else 0
            bit_b = 1 if pixel_value[COLOR.B] >= threshold else 0
            bit = bit_r ^ bit_b

            # Pack the bit into the byte
            byte_red = (byte_red << 1) | bit
            
            bit_count += 1
            
            # Append the byte to the list
            if bit_count == 8:
                bit_array_black.append(byte_black)
                bit_array_red.append(byte_red)
                byte_black = 0
                byte_red = 0
                bit_count = 0
    
    # If there are leftover bits, pad the last byte and append it
    if bit_count > 0:
        byte_black = byte_black << (8 - bit_count)
        byte_red = byte_red << (8 - bit_count)
        bit_array_black.append(byte_black)
        bit_array_red.append(byte_red)
    
    return (bit_array_black, bit_array_red)

def save_image(bit_array, width, height, output_path):
    # Create a new 1-bit image (monochrome) with the specified width and height
    img = Image.new('1', (width, height))
    
    pixels = img.load()
    
    byte_index = 0
    for y in range(height):
        for x in range(0, width, 8):
            if byte_index >= len(bit_array):
                break
            byte = bit_array[byte_index]
            byte_index += 1
            # Set 8 pixels from the byte (most significant bit first)
            for i in range(8):
                if x + i < width:
                    bit = (byte >> (7 - i)) & 1  # Extract bit
                    pixels[x + i, y] = 1 if bit else 0  # Set pixel to white (1) or black (0)
    
    img.save(output_path, 'BMP')


if __name__ == "__main__":
    infile = "test.bmp"
    black, red = extract_image(infile, rotation=90)
    height, width = Image.open("test.bmp").size
    save_image(black, width, height, f"{infile}_black.bmp")
    save_image(red, width, height, f"{infile}_red.bmp")

