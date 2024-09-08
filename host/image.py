from PIL import Image

# NOTE: This works for black (bit_array = extract_channel_to_bit_array("test.bmp", invert=True))
# but not for red 
def extract_channel_to_bit_array(image_path, channel='R', threshold=128, invert=False):
    # Open the image and convert to RGB
    img = Image.open(image_path).convert('RGB')
    
    # Select the channel (R, G, or B)
    if channel == 'R':
        channel_idx = 0
    elif channel == 'G':
        channel_idx = 1
    elif channel == 'B':
        channel_idx = 2
    else:
        raise ValueError("Channel must be 'R', 'G', or 'B'")
    
    # Get the image dimensions
    width, height = img.size
    pixels = img.load()
    
    # Prepare an empty list for the byte-packed binary data
    bit_array = []
    byte = 0
    bit_count = 0
    
    # Loop through every pixel in the image
    for y in range(height):
        for x in range(width):
            # Get the pixel value for the selected channel
            pixel_value = pixels[x, y][channel_idx]
            
            # Convert to a binary bit (0 or 1) based on the threshold
            if invert:
                bit = 1 if pixel_value <= threshold else 0
            else:
                bit = 1 if pixel_value >= threshold else 0

            # # Invert if needed
            # if invert:
            #     bit = 1 - bit
            
            # Pack the bit into the byte
            byte = (byte << 1) | bit
            bit_count += 1
            
            # Once we have 8 bits, append the byte to the list
            if bit_count == 8:
                bit_array.append(byte)
                byte = 0
                bit_count = 0
    
    # If there are leftover bits, pad the last byte and append it
    if bit_count > 0:
        byte = byte << (8 - bit_count)  # Pad the remaining bits with zeros
        bit_array.append(byte)
    
    return bit_array


def save_bit_array_to_bmp(bit_array, width, height, output_path):
    # Create a new 1-bit image (monochrome) with the specified width and height
    img = Image.new('1', (width, height))
    
    # Access the pixel data
    pixels = img.load()
    
    # Iterate over the bit array and set pixels in the new image
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
    
    # Save the image as a BMP file
    img.save(output_path, 'BMP')


if __name__ == "__main__":
    bit_array = extract_channel_to_bit_array("test.bmp", invert=True)

    # Save the bit array as a new BMP file
    width, height = Image.open("test.bmp").size
    save_bit_array_to_bmp(bit_array, width, height, "test.r.bmp")

    # print(", ".join("0x{:02x}".format(x) for x in bit_array))
