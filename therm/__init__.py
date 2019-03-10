import os
from flask import Flask

try:
    import smbus
    import RPi
except ImportError:
    # Replace libraries by fake ones
    import sys
    import fake_rpi

    sys.modules["RPi"] = fake_rpi.RPi  # Fake RPi (GPIO)
    sys.modules["smbus"] = fake_rpi.smbus  # Fake smbus (I2C)

app = Flask(__name__)
env = os.getenv("THERM_ENV", "Development")
app.config.from_object("therm.settings.{}".format(env))

if not app.debug:
    import logging
    from logging.handlers import TimedRotatingFileHandler

    # https://docs.python.org/3.6/library/logging.handlers.html#timedrotatingfilehandler
    file_handler = TimedRotatingFileHandler(os.path.join(app.config["LOG_DIR"], "therm.log"), "midnight")
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter("<%(asctime)s> <%(levelname)s> %(message)s"))
    app.logger.addHandler(file_handler)

import therm.views
