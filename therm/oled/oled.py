
from collections import namedtuple
import time

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


DEMO = True
try:
    import Adafruit_GPIO.SPI as SPI
    import Adafruit_SSD1306

    DEMO = False
except ImportError:
    print("Could not import Adafruit libs; assuming demo mode")


if not DEMO:
    # Raspberry Pi pin configuration:
    RST = None  # on the PiOLED this pin isnt used
    # Note the following are only used with SPI:
    DC = 23
    SPI_PORT = 0
    SPI_DEVICE = 0

    # 128x32 display with hardware I2C:
    disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

    # Initialize library.
    disp.begin()

    # Clear display.
    disp.clear()
    disp.display()


width, height = 128, 32
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0


# Load default font.
font8 = ImageFont.load_default()

# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font8b = ImageFont.truetype("rubik/Rubik-Bold.ttf", 8)
font12n = ImageFont.truetype("antonio/Antonio-Regular.ttf", 12)
font20n = ImageFont.truetype("antonio/Antonio-Regular.ttf", 20)
font10 = ImageFont.truetype("rubik/Rubik-Medium.ttf", 10)
font12 = ImageFont.truetype("rubik/Rubik-Medium.ttf", 12)
font20 = ImageFont.truetype("rubik/Rubik-Light.ttf", 20)
font24 = ImageFont.truetype("rubik/Rubik-Light.ttf", 24)
font32 = ImageFont.truetype("rubik/Rubik-Medium.ttf", 32)
font12b = ImageFont.truetype("rubik/Rubik-Bold.ttf", 12)
font24b = ImageFont.truetype("rubik/Rubik-Bold.ttf", 24)
font32b = ImageFont.truetype("rubik/Rubik-Bold.ttf", 32)


def _draw_weather8(now, soon):
    """Draw weather onto PIL image."""

    image = Image.new("1", (width, height))
    draw = ImageDraw.Draw(image)
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    draw.text((x, top), "{:13}{:13}".format(now.name, soon.name), font=font8, fill=255)
    draw.text((x, top + 8), "{:13}{:13}".format(now.temp, soon.temp), font=font8, fill=255)
    draw.text((x, top + 16), "{:13}{:13}".format(now.wind, soon.wind), font=font8, fill=255)
    draw.text((x, top + 24), "{:13}{:13}".format(now.description, soon.description), font=font8, fill=255)
    # draw.text((x, top+8),     s2, font=font, fill=255)
    # draw.text((x, top+16),    s3,  font=font, fill=255)
    # draw.text((x, top+25),    s4,  font=font, fill=255)
    return image


def _draw_weather24(weather):
    image = Image.new("1", (width, height))
    draw = ImageDraw.Draw(image)
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    draw.text((0, top), "{}: {}".format(weather.name, weather.description.upper()), font=font10, fill=255)
    draw.text((0, top + 11), weather.temp, font=font24b, fill=255)

    windspd, units = weather.wind.split(" ")
    speedwidth = font20n.getsize(windspd)[0]
    unitwidth = font12.getsize(units)[0]
    unitx = width - unitwidth
    speedx = unitx - (speedwidth + 3)
    draw.text((unitx, top + 20), units, font=font12, fill=255)
    draw.text((speedx, top + 11), windspd, font=font20n, fill=255)
    return image


def _draw_status32(temp, setpt):
    image = Image.new("1", (width, height))
    draw = ImageDraw.Draw(image)
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.text((0, top), temp, font=font32b, fill=255)
    setpt_width = font20n.getsize(setpt)[0]
    setpt_x = width - (setpt_width + 3)
    draw.text((setpt_x, top + 6), setpt, font=font20n, fill=255)
    return image


def _display(im):
    if not DEMO:
        disp.image(im)
        disp.display()
    else:
        im.show()


def display(temp, setpt):
    """

    Args:
        temp (str): Inside temperature
        setpt (str): Set point, or "off"

    Returns:

    """
    im = _draw_status32(temp, setpt)
    _display(im)

if __name__ == "__main__":
    display("72.3", "off")
