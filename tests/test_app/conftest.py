from datetime import datetime, timedelta
import itertools
import random

import pytest
from therm import create_app
from therm.models import db, Sample, State


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # create a temporary file to isolate the database for each test
    # db_fd, db_path = tempfile.mkstemp()
    # create the app with common test config
    app = create_app("Test")

    # create the database and load test data
    with app.app_context():
        db.create_all(app=app)

    yield app

    db.drop_all(app=app)


start_time = datetime.strptime("2018-06-01T00:00:00", "%Y-%m-%dT%H:%M:%S")


@pytest.fixture
def fake_samples(app):
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
    with app.app_context():
        for samp in samples_fine:
            db.session.add(samp)
        db.session.commit()
        yield samples_fine


@pytest.fixture
def fake_states(app):
    with app.app_context():
        states = [
            State(time=start_time, set_point=72, set_point_enabled=True),
            State(time=start_time + timedelta(minutes=1), set_point=72, set_point_enabled=True),
        ]
        for state in states:
            db.session.add(state)
        db.session.commit()
        yield states


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()
