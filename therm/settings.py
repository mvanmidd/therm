import os

from . import device_settings


class Default(object):
    POLL_INTERVAL = 60
    """Temp sensor polling interval in seconds."""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_URL = os.environ.get("THERM_DB_URL")
    DB_UNAME = os.environ.get("THERM_DB_UNAME")
    DB_PASS = os.environ.get("THERM_DB_PASS")
    DB_NAME = "therm"
    LOG_DIR = "."

    SQS_QUEUE_NAME = "therm-heartbeat"
    SNS_TOPIC_NAME = "therm-alerts"
    HEARTBEAT_ALARM_NAME = "therm-heartbeat-stopped"
    ALARM_PERIOD = 600

    # Device settings; see device_settings.py for full list
    BUTTONS_ENABLED = False
    TEMP_SENSOR_ENABLED = False
    OLED_ENABLED = False

    def __init__(self):
        self.SQLALCHEMY_DATABASE_URI = "postgresql://{}:{}@{}:5432/{}".format(
            self.DB_UNAME, self.DB_PASS, self.DB_URL, self.DB_NAME
        )
        device_type = os.environ.get("THERM_DEVICE")
        if device_type:
            print("Using settings for device '{}'".format(device_type))
            def props(cls):
                return [i for i in cls.__dict__.keys() if i[:1] != '_']
            setting_names = props(device_settings.DeviceSettingsBase)
            this_device = getattr(device_settings, device_type)
            for param in setting_names:
                setattr(self, param, getattr(this_device, param))
        else:
            print("No THERM_DEVICE found; disabling hardware support")


class Test(Default, device_settings.DeviceSettingsBase):
    ENV = "Test"
    TESTING = True
    DB_NAME = "test"
    POLL_INTERVAL = 0.01

    # Fake the sensors
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

    def __init__(self):
        super().__init__()
        self.SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"


class Development(Default):
    POLL_INTERVAL = 10
    ALARM_PERIOD = 300
    ENV = "Development"
    DEBUG = True


class Production(Default):
    ENV = "Production"
    DEBUG = False
