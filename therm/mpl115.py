"""MPL115 temp sensor functions, adapted from https://www.raspberrypi.org/forums/viewtopic.php?t=91185"""
import time

from flask import current_app
import smbus

# current_app.logger = current_app.logger


# _ADDR and _BUS initialized in init()
_ADDR = None
_BUS = None


def _ctof(c):
    return c * (9.0 / 5.0) + 32


def _read_mpl(addr, bus, debug=False):
    if _BUS is None or _ADDR is None:
        raise ValueError("Bus not initialized; call {}.init(app) to initialize".format(__name__))

    # a0: 16 bits - 1 sign, 12 int, 3 frac
    a0 = (bus.read_byte_data(addr, 0x04) << 8) | bus.read_byte_data(addr, 0x05)
    if a0 & 0x8000:
        a0d = -((~a0 & 0xFFFF) + 1)
    else:
        a0d = a0
    a0f = float(a0d) / 8.0

    # b1: 16 bits - 1 sign, 2 int, 13 frac
    b1 = (bus.read_byte_data(addr, 0x06) << 8) | bus.read_byte_data(addr, 0x07)
    if b1 & 0x8000:
        b1d = -((~b1 & 0xFFFF) + 1)
    else:
        b1d = b1
    b1f = float(b1d) / 8192.0

    # b2: 16 bits - 1 sign, 1 int, 14 frac
    b2 = (bus.read_byte_data(addr, 0x08) << 8) | bus.read_byte_data(addr, 0x09)
    if b2 & 0x8000:
        b2d = -((~b2 & 0xFFFF) + 1)
    else:
        b2d = b2
    b2f = float(b2d) / 16384.0

    # c12: 14 bits - 1 sign, 0 int, 13 frac
    # (Documentation in the datasheet is poor on this.)
    c12 = (bus.read_byte_data(addr, 0x0A) << 8) | bus.read_byte_data(addr, 0x0B)
    if c12 & 0x8000:
        c12d = -((~c12 & 0xFFFF) + 1)
    else:
        c12d = c12
    c12f = float(c12d) / 16777216.0

    # Start conversion and wait 3mS
    bus.write_byte_data(addr, 0x12, 0x0)
    time.sleep(0.003)

    rawpres = (bus.read_byte_data(addr, 0x00) << 2) | (bus.read_byte_data(addr, 0x01) >> 6)
    rawtemp = (bus.read_byte_data(addr, 0x02) << 2) | (bus.read_byte_data(addr, 0x03) >> 6)

    pcomp = a0f + (b1f + c12f * rawtemp) * rawpres + b2f * rawtemp
    pkpa = pcomp / 15.737 + 50

    temp = 25.0 - (rawtemp - 498.0) / 5.35
    if debug:
        current_app.logger.info("\nRaw pres = 0x%3x %4d" % (rawpres, rawpres))
        current_app.logger.info("Raw temp = 0x%3x %4d" % (rawtemp, rawtemp))
        current_app.logger.info("Pres = %3.2f kPa" % pkpa)
        current_app.logger.info("Temp = %3.2f c, %3.2f f" % (temp, _ctof(temp)))
    return _ctof(temp), pkpa


def read(debug=False):
    """Read temp and humidity from sensor.

    Args:
        debug:

    Returns:
        tuple(float, float): temperature, humidity

    """
    if _BUS is None or _ADDR is None:
        raise ValueError("Bus not initialized; call {}.init(app) to initialize".format(__name__))
    temp, humidity = _read_mpl(addr=_ADDR, bus=_BUS, debug=debug)
    temp += _TEMP_CALIB_F
    return temp, humidity


def init_app(app):
    global _BUS_ID, _BUS, _ADDR, _TEMP_CALIB_F
    _BUS_ID = app.config["TEMP_SENSOR_BUS_ID"]
    _ADDR = app.config["TEMP_SENSOR_ADDR"]
    _TEMP_CALIB_F = app.config["TEMP_CALIB_F"]
    _BUS = smbus.SMBus(_BUS_ID)


if __name__ == "__main__":
    read(debug=True)
