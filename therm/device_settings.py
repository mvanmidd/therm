"""Device-specific settings for therm.

This is mostly useful for hardware settings: GPIO pins, screens, sensors, etc.

These classes will be imported into settings.py based on the THERM_DEVICE environment variable.
"""

class DeviceSettingsBase(object):
    BUTTONS_ENABLED = False
    PIN_TEMP_ON_OFF = None
    PIN_TEMP_DOWN = None
    PIN_TEMP_UP = None
    PIN_TEMP_HOLD = None

    TEMP_SENSOR_ENABLED = False
    TEMP_SENSOR_ADDR = None
    TEMP_SENSOR_BUS_ID = None
    TEMP_CALIB_F = None

    OLED_ENABLED = False
    SSD1306_I2C_ADDRESS = 0

    RELAY_ENABLED = False
    RELAY_GPIO = 0

class Primary(DeviceSettingsBase):
    """Full size pi 2 B+ with 2.2" TFT hat, temp sensor, and relay control."""

    BUTTONS_ENABLED = True
    PIN_TEMP_ON_OFF = 17
    PIN_TEMP_DOWN = 22
    PIN_TEMP_UP = 23
    PIN_TEMP_HOLD = 27


    TEMP_SENSOR_ENABLED = True
    TEMP_SENSOR_ADDR = 0x60
    TEMP_SENSOR_BUS_ID = 1
    TEMP_CALIB_F = 3.0
    """Adjustment to temp sensor, in degrees Farenheit"""

    OLED_ENABLED = False

    RELAY_ENABLED = True
    RELAY_GPIO = 4  # GPIO 4, Physical pin 7 on raspi. LOW turns relay on.

class Zero(DeviceSettingsBase):
    """Pi Zero with OLED screen"""

    BUTTONS_ENABLED = False
    PIN_TEMP_ON_OFF = 17
    PIN_TEMP_DOWN = 22
    PIN_TEMP_UP = 23
    PIN_TEMP_HOLD = 27


    TEMP_SENSOR_ENABLED = True
    TEMP_SENSOR_ADDR = 0x60
    TEMP_SENSOR_BUS_ID = 1
    TEMP_CALIB_F = 3.0
    """Adjustment to temp sensor, in degrees Farenheit"""

    OLED_ENABLED = False
    SSD1306_I2C_ADDRESS = 0x3C

    RELAY_ENABLED = True
    RELAY_GPIO = 4  # GPIO 4, Physical pin 7 on raspi. LOW turns relay on.
