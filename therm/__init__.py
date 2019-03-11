import itertools
import os
import random
from datetime import datetime, timedelta
import time
import click
from flask.cli import with_appcontext

from therm import settings, relay, buttons
from flask import Flask, current_app, copy_current_request_context

from therm.models import Sample, State, db

try:
    import smbus
    import RPi
except ImportError:
    # Replace libraries by fake ones
    import sys
    import fake_rpi

    sys.modules["RPi"] = fake_rpi.RPi  # Fake RPi (GPIO)
    sys.modules["smbus"] = fake_rpi.smbus  # Fake smbus (I2C)



POLL_INTERVAL = 5
"""Temp sensor polling interval in seconds."""
POLL_LOCKFILE = "/tmp/polling"
"""Lock file for polling process."""
TEMP_WINDOW = 1
"""Only adjust thermostat when temp is outside range of target +/- TEMP_WINDOW."""


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

    @app.cli.command("poll")
    @with_appcontext
    @click.option("--force", is_flag=True, default=False)
    def poll_temp_sensor(force):
        """Poll temp sensor indefinitely, writing results to DB."""
        from therm.mpl115 import read

        if os.path.exists(POLL_LOCKFILE):
            lock_datetime = open(POLL_LOCKFILE, "r").read()
            if force or click.confirm("Found a lockfile from {}; delete it?".format(lock_datetime.strip())):
                os.remove(POLL_LOCKFILE)
            else:
                sys.exit(0)

        with open(POLL_LOCKFILE, "w") as lockfile:
            lockfile.write(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
            click.echo("Obtained lock at {}".format(POLL_LOCKFILE))

        relay.init()
        buttons.init()

        def on_off():
            """Handle on/off button."""
            relay.flip()
        buttons.register_on_off(relay.flip)

        n_read = 0
        try:
            while True:
                # Poll sensor
                temp, pressure = read()
                sample = Sample(temp=temp, pressure=pressure)
                db.session.add(sample)
                db.session.commit()
                n_read += 1
                click.echo("Read {} samples".format(n_read))

                # React to desired state
                latest_state = State.latest()
                if latest_state:
                    if latest_state.set_point > (temp + TEMP_WINDOW):
                        click.echo("Target {}; temp {}: THERM ON".format(latest_state.set_point, temp))
                        relay.on()
                    elif latest_state.set_point < (temp - TEMP_WINDOW):
                        click.echo("Target {}; temp {}: THERM OFF".format(latest_state.set_point, temp))
                        relay.off()
                else:
                    click.echo("Not performing thermostat control; no target found")

                time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            os.remove(POLL_LOCKFILE)
            buttons.cleanup()
            click.echo("Removed lock... goodbye!")

    @app.cli.command("populate-db")
    @with_appcontext
    def populate_db_command():
        """Populate the DB with some test data."""
        start_time = datetime.strptime("2018-06-01T00:00:00", "%Y-%m-%dT%H:%M:%S")
        samples_coarse = [
            Sample(temp=random.randrange(40, 80), time=start_time + timedelta(hours=i)) for i in range(10)
        ]
        samples_fine = list(
            itertools.chain.from_iterable(
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
            )
        )
        for samp in samples_fine:
            db.session.add(samp)
        click.echo("Added {} Samples to db {}".format(len(samples_fine), current_app.config["DB_URL"]))

        state = State(set_point=72, set_point_enabled=True)
        db.session.add(state)
        click.echo("Added 1 State to db {}".format(current_app.config["DB_URL"]))
        db.session.commit()

    @app.cli.command("truncate-db")
    @with_appcontext
    def truncate_db_command():
        """Truncate db tables."""
        tables = [Sample, State]
        for table in tables:
            db.session.query(table).delete()
        click.echo("Truncated {}".format(", ".join([t.__table__.name  for t in tables])))

    @app.cli.command("drop-db")
    @with_appcontext
    def drop_db_command():
        """Drop all tables."""
        db.drop_all()
        click.echo("Dropped {}.".format(current_app.config["DB_URL"]))

    @app.cli.command("init-db")
    @with_appcontext
    def init_db_command():
        """Clear existing data and create new tables."""
        db.create_all()
        click.echo("Initialized {}.".format(current_app.config["DB_URL"]))

    return app
