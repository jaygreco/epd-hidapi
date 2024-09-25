import logging
from datetime import datetime
from enum import IntEnum

import PIL.Image
import PIL.ImageOps


class COLOR(IntEnum):
    R = 0
    G = 1
    B = 2


class Image:
    def __init__(self, image_path):
        self.logger = logging.getLogger(__name__)
        self.img = PIL.Image.open(image_path)
        self.__set_size(self.img.size)

    def __set_size(self, size):
        self.width, self.height = size
        self.size = size

    def rotate(self, rotation):
        self.logger.info(f"Rotating image by {rotation}*")
        self.img = self.img.rotate(rotation, expand=True)
        self.__set_size(self.img.size)

    def resize(self, width, height):
        self.logger.info(f"Resizing image to {(width, height)}")

        self.img = PIL.ImageOps.fit(self.img, (width, height))
        self.__set_size((width, height))

    def extract(self, threshold=128):
        start = datetime.now()

        self.logger.info("Extracting red/black pixels from image")

        pixels = self.img.load()

        # Prepare an empty list for the byte-packed binary data
        bit_array_black = []
        byte_black = 0
        bit_array_red = []
        byte_red = 0
        bit_count = 0

        width, height = self.size
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

        self.bit_array_black = bit_array_black
        self.bit_array_red = bit_array_red

        self.logger.info(f"Done. Process took {datetime.now()-start}")

    def save(self, output_path, monochrome=False, color="black"):
        if monochrome:
            if not self.bit_array_red and self.bit_array_black:
                self.logger.error("Run image.extract() before saving bitmaps!")
                return

            # Create a new 1-bit image (monochrome) with the specified width and height
            img = PIL.Image.new('1', self.size)
            pixels = img.load()

            bit_array = self.bit_array_black if color == "black" else self.bit_array_red

            byte_index = 0
            for y in range(self.height):
                for x in range(0, self.width, 8):
                    if byte_index >= len(bit_array):
                        break
                    byte = bit_array[byte_index]
                    byte_index += 1
                    # Set 8 pixels from the byte (most significant bit first)
                    for i in range(8):
                        if x + i < self.width:
                            bit = (byte >> (7 - i)) & 1  # Extract bit
                            # Set pixel to white (1) or black (0)
                            pixels[x + i, y] = 1 if bit else 0

            self.logger.info(
                f"Saving monochrome ({color}) image to {output_path}")
            img.save(output_path, 'BMP')

        else:
            self.logger.info(f"Saving image to {output_path}")
            img = self.img
            img.save(output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    infile = "test.bmp"

    image = Image(infile)
    image.resize(width=768, height=960)
    image.save(f"{infile}_resized.png")

    image.rotate(rotation=90)
    image.extract(threshold=200)
    image.save(f"{infile}_black.bmp", monochrome=True, color="black")
    image.save(f"{infile}_red.bmp", monochrome=True, color="red")
