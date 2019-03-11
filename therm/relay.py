try:
    import smbus
    import RPi
except ImportError:
    # Replace libraries by fake ones
    import sys
    import fake_rpi

    sys.modules["RPi"] = fake_rpi.RPi  # Fake RPi (GPIO)
    sys.modules["smbus"] = fake_rpi.smbus  # Fake smbus (I2C)
    import RPi

from RPi import GPIO


HEAT_GPIO = 4  # GPIO 4, Physical pin 7 on raspi. LOW turns relay on.


def init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(HEAT_GPIO, GPIO.OUT)


def on():
    GPIO.output(HEAT_GPIO, GPIO.LOW)


def off():
    GPIO.output(HEAT_GPIO, GPIO.HIGH)  # out


def is_on():
    return not GPIO.input(HEAT_GPIO)

def flip():
    if is_on():
        off()
    else:
        on()
