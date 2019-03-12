import os


# Import fake rpi libraries if we're not on a raspberry pi
try:
    import smbus
    import RPi
except ImportError:
    import sys
    import fake_rpi

    # by default it prints everything to std.error
    fake_rpi.toggle_print(False)  # turn off printing
    #
    # from therm.relay import HEAT_GPIO
    # from random import randint
    #
    # # Monkeypatch smbus.GPIO to preserve state of heater i/o pin
    # class MyGPIO(fake_rpi.RPi._GPIO):
    #     heater_state = 0
    #
    #     def input(self, a):
    #         print("CALLED")
    #         if a == HEAT_GPIO:
    #             return self.heater_state
    #         else:
    #             return randint(0, 1)
    #
    #     def output(self, channel, state):
    #         print("CALLED")
    #         if channel == HEAT_GPIO:
    #             self.heater_state = state
    #
    # fake_rpi.RPi.GPIO = MyGPIO()

    sys.modules["RPi"] = fake_rpi.RPi  # Fake RPi (GPIO)
    sys.modules["smbus"] = fake_rpi.smbus  # Fake smbus (I2C)

    import RPi
    import smbus


from flask import Flask

from therm.models import Sample, State, db
from therm import settings, relay, buttons

# Flask-sqlalchemy has some deprecationwarnings; squish em https://github.com/pallets/flask-sqlalchemy/issues/671
import warnings
from sqlalchemy import exc

warnings.filterwarnings("ignore", category=exc.SADeprecationWarning)
warnings.filterwarnings("ignore", message="The psycopg2 wheel package will be renamed from release 2.8")


def create_app(config_env=None):
    app = Flask(__name__)
    env = config_env or os.getenv("THERM_ENV", "Development")
    app_settings = getattr(settings, env)
    app.config.from_object(app_settings())

    if not app.debug:
        import logging
        from logging.handlers import TimedRotatingFileHandler

        # https://docs.python.org/3.6/library/logging.handlers.html#timedrotatingfilehandler
        file_handler = TimedRotatingFileHandler(os.path.join(app.config["LOG_DIR"], "therm.log"), "midnight")
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(logging.Formatter("<%(asctime)s> <%(levelname)s> %(message)s"))
        app.logger.addHandler(file_handler)

    app.logger.warning("Loaded app with settings: {}".format(env))

    from .models import db

    db.init_app(app)

    import therm.views as _views

    app.register_blueprint(_views.root)

    from .cli import init_app

    init_app(app)

    return app
