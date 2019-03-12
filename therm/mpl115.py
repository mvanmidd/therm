"""MPL115 temp sensor functions, adapted from https://www.raspberrypi.org/forums/viewtopic.php?t=91185"""
import time

from flask import current_app
import smbus

# current_app.logger = current_app.logger


_ADDR = 0x60
_BUS_ID = 1

_TEMP_CALIB_F = 3.0
"""Adjustment to temp sensor, in degrees Farenheit"""

_BUS = smbus.SMBus(_BUS_ID)

def _ctof(c):
    return c * (9.0 / 5.0) + 32


def _read_mpl(addr=_ADDR, debug=False):

    # a0: 16 bits - 1 sign, 12 int, 3 frac
    a0 = (_BUS.read_byte_data(addr, 0x04) << 8) | _BUS.read_byte_data(addr, 0x05)
    if a0 & 0x8000:
        a0d = -((~a0 & 0xFFFF) + 1)
    else:
        a0d = a0
    a0f = float(a0d) / 8.0

    # b1: 16 bits - 1 sign, 2 int, 13 frac
    b1 = (_BUS.read_byte_data(addr, 0x06) << 8) | _BUS.read_byte_data(addr, 0x07)
    if b1 & 0x8000:
        b1d = -((~b1 & 0xFFFF) + 1)
    else:
        b1d = b1
    b1f = float(b1d) / 8192.0

    # b2: 16 bits - 1 sign, 1 int, 14 frac
    b2 = (_BUS.read_byte_data(addr, 0x08) << 8) | _BUS.read_byte_data(addr, 0x09)
    if b2 & 0x8000:
        b2d = -((~b2 & 0xFFFF) + 1)
    else:
        b2d = b2
    b2f = float(b2d) / 16384.0

    # c12: 14 bits - 1 sign, 0 int, 13 frac
    # (Documentation in the datasheet is poor on this.)
    c12 = (_BUS.read_byte_data(addr, 0x0A) << 8) | _BUS.read_byte_data(addr, 0x0B)
    if c12 & 0x8000:
        c12d = -((~c12 & 0xFFFF) + 1)
    else:
        c12d = c12
    c12f = float(c12d) / 16777216.0

    # Start conversion and wait 3mS
    _BUS.write_byte_data(addr, 0x12, 0x0)
    time.sleep(0.003)

    rawpres = (_BUS.read_byte_data(addr, 0x00) << 2) | (_BUS.read_byte_data(addr, 0x01) >> 6)
    rawtemp = (_BUS.read_byte_data(addr, 0x02) << 2) | (_BUS.read_byte_data(addr, 0x03) >> 6)

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
    temp, humidity = _read_mpl(debug=debug)
    temp += _TEMP_CALIB_F
    return temp, humidity


if __name__ == "__main__":
    read(debug=True)
