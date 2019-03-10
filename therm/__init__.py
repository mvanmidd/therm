import itertools
import os
import random
from datetime import datetime, timedelta

import click
from flask.cli import with_appcontext

from therm import settings
from flask import Flask, current_app

from therm.models import Sample, db

try:
    import smbus
    import RPi
except ImportError:
    # Replace libraries by fake ones
    import sys
    import fake_rpi

    sys.modules["RPi"] = fake_rpi.RPi  # Fake RPi (GPIO)
    sys.modules["smbus"] = fake_rpi.smbus  # Fake smbus (I2C)


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

    app.logger.info("Loaded app with settings: {}".format(env))

    # Initialize db
    from .models import db

    db.init_app(app)

    import therm.views as _views
    app.register_blueprint(_views.root)

    @app.cli.command('populate-db')
    @with_appcontext
    def populate_db_command():
        """Clear existing data and create new tables."""
        start_time = datetime.strptime("2018-06-01T00:00:00", "%Y-%m-%dT%H:%M:%S")
        samples_coarse = [
            Sample(temp=random.randrange(40, 80), time=start_time + timedelta(hours=i)) for i in range(10)
        ]
        samples_fine = list(itertools.chain.from_iterable(
            [
                [
                    Sample(
                        temp=samp.temp + random.random(),
                        time=samp.time + timedelta(minutes=10 * i + random.randrange(-4, 4)),
                    )
                    for i in range(1, 6)
                ]
                for samp in samples_coarse
            ]
        ))
        for samp in samples_fine:
            db.session.add(samp)
        db.session.commit()
        click.echo("Added {} samples to db {}".format(len(samples_fine), current_app.config["DB_URL"]))


    @app.cli.command('init-db')
    @with_appcontext
    def init_db_command():
        """Clear existing data and create new tables."""
        db.create_all()
        click.echo('Initialized the database.')

    return app
