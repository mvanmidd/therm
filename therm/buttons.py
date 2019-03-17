"""Button initialization and callbacks.

Based on https://raspi.tv/2013/how-to-use-interrupts-with-python-on-the-raspberry-pi-and-rpi-gpio-part-3.
"""
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

from flask import current_app
from RPi import GPIO



def init(app):
    for pin in (app.config['PIN_TEMP_DOWN'], app.config['PIN_TEMP_UP'], app.config['PIN_TEMP_ON_OFF']):
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def register_on_off(callback):
    GPIO.add_event_detect(current_app.config['PIN_TEMP_ON_OFF'], GPIO.FALLING, callback=lambda _: callback(), bouncetime=300)


def register_temp_up(callback):
    GPIO.add_event_detect(current_app.config['PIN_TEMP_UP'], GPIO.FALLING, callback=lambda _: callback(), bouncetime=300)


def register_temp_down(callback):
    GPIO.add_event_detect(current_app.config['PIN_TEMP_DOWN'], GPIO.FALLING, callback=lambda _: callback(), bouncetime=300)


def register_temp_hold(callback):
    GPIO.add_event_detect(current_app.config['PIN_TEMP_HOLD'], GPIO.FALLING, callback=lambda _: callback(), bouncetime=300)


def cleanup():
    GPIO.cleanup()
