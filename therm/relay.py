try:
    import smbus
    import RPi
    from RPi import GPIO
except ImportError:
    # Replace libraries by fake ones
    import sys
    import fake_rpi

    sys.modules["RPi"] = fake_rpi.RPi  # Fake RPi (GPIO)
    sys.modules["smbus"] = fake_rpi.smbus  # Fake smbus (I2C)
    import RPi
    from RPi import GPIO


HEAT_GPIO = None


def init(heat_gpio):
    global HEAT_GPIO
    HEAT_GPIO = heat_gpio
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(HEAT_GPIO, GPIO.OUT)


def on():
    GPIO.output(HEAT_GPIO, GPIO.LOW)


def off():
    GPIO.output(HEAT_GPIO, GPIO.HIGH)  # out


def is_on():
    return not GPIO.input(HEAT_GPIO)


def flip():
    """Flip the heater state and return new state."""
    if is_on():
        off()
        return False
    else:
        on()
        return True
