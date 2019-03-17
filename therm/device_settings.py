"""Device-specific settings for therm.

This is mostly useful for hardware settings: GPIO pins, screens, sensors, etc.

These classes will be imported into settings.py based on the THERM_DEVICE environment variable.
"""

class Bedroom(object):
    """Full size pi 2 B+ with 2.2" TFT hat, temp sensor, and relay control."""

    PIN_TEMP_ON_OFF = 17
    PIN_TEMP_DOWN = 22
    PIN_TEMP_UP = 23
    PIN_TEMP_HOLD = 27

