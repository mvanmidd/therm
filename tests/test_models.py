import pytest
import itertools
from datetime import datetime, timedelta
import random
from therm.models import db, Sample, State

START_TIME = datetime.strptime("2018-06-01T00:00:00", "%Y-%m-%dT%H:%M:%S")
END_TIME = START_TIME + timedelta(hours=10)


@pytest.fixture
def fake_samples(app):
    """590 minute time range, with samples every 10min with +/-4min jitter"""
    samples_coarse = [
        Sample(temp=random.randrange(40, 80), time=START_TIME + timedelta(hours=i)) for i in range(10)
    ]
    samples_fine = list(itertools.chain.from_iterable(
        [
            [
                Sample(
                    temp=samp.temp + random.random(),
                    time=samp.time + timedelta(minutes=10 * i + random.randrange(-4, 4)),
                )
                for i in range(0, 6)
            ]
            for samp in samples_coarse
        ]
    ))
    with app.app_context():
        for samp in samples_fine:
            db.session.add(samp)
        db.session.commit()
        yield samples_fine


def test_since(app, fake_samples):
    latest = Sample.since(END_TIME-timedelta(minutes=15))
    ts = Sample.timeseries(latest)
    assert len(ts.data) == 1

def test_latest(app, fake_samples):
    latest = Sample.latest(limit=10)
    assert len(latest) == 10
    ts = Sample.timeseries(latest)
    assert list(ts.data) == [s.temp for s in latest]
    tmin, tmax = min(ts.index), max(ts.index)
    assert tmin < tmax
    assert END_TIME - timedelta(minutes=104) <= tmin < END_TIME - timedelta(minutes=96)
    assert END_TIME - timedelta(minutes=14) <= tmax < END_TIME - timedelta(minutes=6)
    resampled = ts.resample('60S')
    assert 82 <= len(resampled.mean().index) <= 98
    assert all([40 <= t <= 80 for t in resampled.interpolate(method='linear')])

def test_update_state(app, fake_state):
    latest = State.latest()
    State.update_state('set_point_enabled', not latest.set_point_enabled)
    new_state = State.latest()
    assert new_state.set_point_enabled != latest.set_point_enabled
    assert latest
    assert latest.id != new_state.id

def test_timeseries(app, fake_samples):
    latest = Sample.latest(limit=len(fake_samples))
    assert len(latest) == len(fake_samples)
    ts = Sample.timeseries(latest)
    assert list(ts.data) == [s.temp for s in latest]
    tmin, tmax = min(ts.index), max(ts.index)
    assert tmin < tmax
    assert START_TIME - timedelta(minutes=4) <= tmin < START_TIME + timedelta(minutes=4)
    assert END_TIME - timedelta(minutes=14) <= tmax < END_TIME - timedelta(minutes=6)
    resampled = ts.resample('60S')
    assert 582 <= len(resampled.mean().index) <= 598
    assert all([40 <= t <= 80 for t in resampled.interpolate(method='linear')])

def test_get_states(app, fake_state):
    latest = State.latest()
    assert latest
    assert latest.id == fake_state.id

