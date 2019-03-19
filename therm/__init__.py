import os
import warnings

from flask import Flask

# Import fake rpi libraries if we're not on a raspberry pi
try:
    import smbus
    import RPi
except ImportError:
    import sys
    import fake_rpi

    # by default it prints everything to std.error
    fake_rpi.toggle_print(False)  # turn off printing

    sys.modules["RPi"] = fake_rpi.RPi  # Fake RPi (GPIO)
    sys.modules["smbus"] = fake_rpi.smbus  # Fake smbus (I2C)

    import RPi
    import smbus


from therm.models import Sample, State, db
from therm import settings, relay, buttons

# Flask-sqlalchemy has some deprecationwarnings; squish em https://github.com/pallets/flask-sqlalchemy/issues/671
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

    import json

    def jsonfilter(value):
        if isinstance(value, str):
            return value
        return json.dumps(value)

    app.jinja_env.filters['json'] = jsonfilter

    app.logger.warning("Loaded app with settings: {}".format(env))

    from .models import db

    db.init_app(app)

    import therm.views as _views

    app.register_blueprint(_views.root)

    from .cli import init_app as cli_init

    cli_init(app)

    # Temp sensor control moved to cli.py
    # from .mpl115 import init_app as mpl_init
    # mpl_init(app)


    return app
