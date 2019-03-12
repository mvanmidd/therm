import itertools
import os
import random
import sys
import time
from datetime import datetime, timedelta

import click
from flask import current_app
from flask.cli import with_appcontext

from therm import relay, buttons
from therm.models import Sample, db, State
from therm.mpl115 import read

POLL_INTERVAL = 5
"""Temp sensor polling interval in seconds."""
POLL_LOCKFILE = "/tmp/polling"
"""Lock file for polling process."""
TEMP_WINDOW = 1
"""Only adjust thermostat when temp is outside range of target +/- TEMP_WINDOW."""


def _poll_once():
    """The main poll / update loop to run on raspberry pi."""
    # Poll sensor
    temp, pressure = read()
    sample = Sample(temp=temp, pressure=pressure)
    db.session.add(sample)
    db.session.commit()

    # React to desired state
    latest_state = State.latest()
    if not latest_state:
        click.echo("Not performing thermostat control; no target found")
        return

    if latest_state.set_point > (temp + TEMP_WINDOW) and State.update_state("heat_on", True):
        click.echo("Target {}; temp {}: THERM ON".format(latest_state.set_point, temp))
        relay.on()
    elif latest_state.set_point < (temp - TEMP_WINDOW) and State.update_state("heat_on", False):
        click.echo("Target {}; temp {}: THERM OFF".format(latest_state.set_point, temp))
        relay.off()


def _register_buttons():
    """Register callbacks for the buttons on the raspi."""

    def on_off():
        """Handle on/off button."""
        if State.update_state("set_point_enabled", False):
            click.echo("Manual update to heater state; disabling set point.")
        relay.flip()

    buttons.register_on_off(relay.flip)


def _validate_state():
    """Ensure that current relay state matches current DB state."""
    latest = State.latest()
    relay_state = relay.is_on()
    if latest.heat_on != relay_state:
        click.echo(
            "Warning: DB state (heat_on = {} as of {}) does not match relay state is_on={}. Updating DB.".format(
                latest.heat_on, latest.time.isoformat(), relay_state
            )
        )
        State.update_state('heat_on', relay_state)


@click.command("poll")
@with_appcontext
@click.option("--force", is_flag=True, default=False)
def poll_temp_sensor(force):
    """Poll temp sensor indefinitely, writing results to DB."""

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
    n_read = 0
    try:
        while True:
            _poll_once()
            _validate_state()
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        os.remove(POLL_LOCKFILE)
        buttons.cleanup()
        click.echo("Removed lock... goodbye!")


@click.command("populate-db")
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


@click.command("truncate-db")
@with_appcontext
def truncate_db_command():
    """Truncate db tables."""
    tables = [Sample, State]
    for table in tables:
        db.session.query(table).delete()
    click.echo("Truncated {}".format(", ".join([t.__table__.name for t in tables])))


@click.command("drop-db")
@with_appcontext
def drop_db_command():
    """Drop all tables."""
    db.drop_all()
    click.echo("Dropped {}.".format(current_app.config["DB_URL"]))


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    db.create_all()
    click.echo("Initialized {}.".format(current_app.config["DB_URL"]))


def init_app(app):
    for cmd in (poll_temp_sensor, populate_db_command, truncate_db_command, drop_db_command, init_db_command):
        app.cli.add_command(cmd)
