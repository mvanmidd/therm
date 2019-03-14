import asyncio
import itertools
import json
import os
import random
import sys
from datetime import datetime, timedelta

import click
from flask import current_app
from flask.json import dumps
from flask.cli import with_appcontext
import boto3

from . import relay, buttons, mpl115
from .models import Sample, db, State

POLL_LOCKFILE = "/tmp/polling"
"""Lock file for polling process."""
TEMP_WINDOW = 1
"""Only adjust thermostat when temp is outside range of target +/- TEMP_WINDOW."""
TEMP_INCREMENT = 0.5
"""Increment for up/down buttons."""

loop = asyncio.get_event_loop()


def _poll_once(to_sqs=False):
    """The main poll / update loop to run on raspberry pi."""
    # Poll sensor
    temp, pressure = mpl115.read()
    sample = Sample(temp=temp, pressure=pressure)
    db.session.add(sample)
    db.session.commit()

    if to_sqs:
        sqs_client = boto3.client("sqs")
        response = sqs_client.send_message(
            QueueUrl="https://sqs.us-east-1.amazonaws.com/{}/{}".format(
                get_account_id(), current_app.config["SQS_QUEUE_NAME"]
            ),
            MessageBody=dumps(sample._asdict()),
        )
        click.echo("Sent to SQS")
        click.echo(dumps(response))

    # React to desired state
    latest_state = State.latest()
    if not latest_state:
        click.echo("Not performing thermostat control; no target found")
        return

    click.echo("Target {}; temp {}".format(latest_state.set_point, temp))
    if latest_state.set_point_enabled:
        if latest_state.set_point > (temp + TEMP_WINDOW) and State.update_state("heat_on", True):
            click.echo("Target {}; temp {}: THERM ON".format(latest_state.set_point, temp))
            relay.on()
        elif latest_state.set_point < (temp - TEMP_WINDOW) and State.update_state("heat_on", False):
            click.echo("Target {}; temp {}: THERM OFF".format(latest_state.set_point, temp))
            relay.off()


async def _poll_forever(to_sqs=False):
    while True:
        _poll_once(to_sqs)
        _validate_state()
        await asyncio.sleep(current_app.config["POLL_INTERVAL"])


def on_off():
    """Handle on/off button."""
    if State.update_state("set_point_enabled", False):
        click.echo("Manual update to heater state; disabling set point.")
    State.update_state("heat_on", relay.flip())
    click.echo("New state: {}".format(State.latest()))


def _adjust_temp(delta):
    latest = State.latest()
    State.update_state("set_point", latest.set_point + delta)
    if State.update_state("set_point_enabled", True):
        click.echo("Temperature adjusted with set point disabled, enabling set point.")


def up():
    """Handle temperature up button."""
    _adjust_temp(TEMP_INCREMENT)


def down():
    """Handle temperature down button."""
    _adjust_temp(TEMP_INCREMENT * -1.0)


def _register_buttons():
    """Register callbacks for the buttons on the raspi."""
    buttons.register_on_off(lambda: loop.call_soon_threadsafe(on_off))
    buttons.register_temp_up(lambda: loop.call_soon_threadsafe(up))
    buttons.register_temp_down(lambda: loop.call_soon_threadsafe(down))


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
        State.update_state("heat_on", relay_state)
    else:
        State.refresh()


def _setup():

    relay.init()
    buttons.init()
    _register_buttons()


@click.command("poll")
@with_appcontext
@click.option("--force", is_flag=True, default=False)
@click.option("--reset/--no-reset", default=True)
@click.option("--to-sqs", is_flag=True, default=False)
def poll_temp_sensor(force, reset, to_sqs):
    """Poll temp sensor indefinitely, writing results to DB.\

    Args:
        force (bool): Force overwrite lockfile.
        reset (bool): Reset heat relay and set point to False on start.
        to_sqs (bool): whether to also publish Samples to SQS

    """

    if os.path.exists(POLL_LOCKFILE):
        lock_datetime = open(POLL_LOCKFILE, "r").read()
        if force or click.confirm("Found a lockfile from {}; delete it?".format(lock_datetime.strip())):
            os.remove(POLL_LOCKFILE)
        else:
            sys.exit(0)

    with open(POLL_LOCKFILE, "w") as lockfile:
        lockfile.write(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
        click.echo("Obtained lock at {}".format(POLL_LOCKFILE))

    _setup()
    if reset:
        click.echo("Resetting state.")
        if State.update_state("set_point_enabled", False):
            click.echo("Disabling set point")
        relay.off()
        State.update_state("heat_on", False)
    task = loop.create_task(_poll_forever(to_sqs))

    try:
        loop.run_until_complete(task)

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


def get_account_id():
    # suggested by https://groups.google.com/forum/#!topic/boto-users/QhASXlNBm40
    return boto3.client("sts").get_caller_identity().get("Account")


def _arn(service, resource):
    # TODO: multi-region?
    return "arn:aws:{}:{}:{}:{}".format(service, "us-east-1", get_account_id(), resource)


def create_sqs_no_messages_alarm():
    """Alarm when no SQS messages received by queue for one ALARM_PERIOD
    """
    cloudwatch_client = boto3.client("cloudwatch")
    cloudwatch_client.put_metric_alarm(
        AlarmName=current_app.config["HEARTBEAT_ALARM_NAME"],
        AlarmDescription="therm heartbeat stopped!",
        ActionsEnabled=True,
        OKActions=[_arn("sns", current_app.config["SNS_TOPIC_NAME"])],
        AlarmActions=[_arn("sns", current_app.config["SNS_TOPIC_NAME"])],
        InsufficientDataActions=[_arn("sns", current_app.config["SNS_TOPIC_NAME"])],
        TreatMissingData="breaching",
        MetricName="NumberOfMessagesSent",
        Namespace="AWS/SQS",
        Statistic="Sum",
        Dimensions=[{"Name": "QueueName", "Value": current_app.config["SQS_QUEUE_NAME"]}],
        Period=current_app.config["ALARM_PERIOD"],
        Unit="Seconds",
        EvaluationPeriods=1,
        Threshold=1,
        ComparisonOperator="LessThanOrEqualToThreshold",
    )

@click.command("unset")
@with_appcontext
def unset_hold():
    """Unset set point."""
    State.update_state('set_point_enabled', False)
    click.echo(State.latest())

@click.command("set")
@with_appcontext
@click.argument("temp", type=int, required=True)
def set_hold(temp):
    """Enable set point, and set desired temp to `temp`

    Args:
        temp (int): New temp

    """
    State.update_state('set_point', temp)
    State.update_state('set_point_enabled', True)
    click.echo(State.latest())

@click.command("state")
@with_appcontext
def state():
    """Print state."""
    click.echo(State.latest())



@click.command("create-alarms")
@with_appcontext
@click.option("--sns", is_flag=True, default=False)
def create_alarms_command(sns):
    """Clear existing data and create new tables.

    Args:
        sns (bool): Whether to create SNS topic.

    """
    if sns:
        sns_client = boto3.client("sns")
        sns_arn = sns_client.create_topic(Name=current_app.config["SNS_TOPIC_NAME"])
        click.echo("Created {}".format(sns_arn))
    sqs_client = boto3.client("sqs")
    sqs_arn = sqs_client.create_queue(QueueName=current_app.config["SQS_QUEUE_NAME"])
    click.echo("Created {}".format(sqs_arn))
    create_sqs_no_messages_alarm()
    click.echo("Created {}".format(current_app.config["HEARTBEAT_ALARM_NAME"]))


def init_app(app):
    for cmd in (
        poll_temp_sensor,
        populate_db_command,
        truncate_db_command,
        drop_db_command,
        init_db_command,
        create_alarms_command,
        set_hold,
        unset_hold,
        state,
    ):
        app.cli.add_command(cmd)
