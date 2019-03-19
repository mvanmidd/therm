import pytest
import itertools
from datetime import datetime, timedelta
import random
from therm.models import db, Sample, State, jointerpolate

START_TIME = datetime.strptime("2018-06-01T00:00:00", "%Y-%m-%dT%H:%M:%S")
END_TIME = START_TIME + timedelta(hours=10)


@pytest.fixture
def fake_states(app):
    """590 minute time range, with states every 10min with +/-4min jitter"""
    states_coarse = [
        State(set_point=random.randrange(40, 80), time=START_TIME + timedelta(hours=i)) for i in range(10)
    ]
    states_fine = list(itertools.chain.from_iterable(
        [
            [
                State(
                    set_point=samp.set_point + random.random(),
                    time=samp.time + timedelta(minutes=10 * i + random.randrange(-4, 4)),
                )
                for i in range(0, 6)
            ]
            for samp in states_coarse
        ]
    ))
    with app.app_context():
        for samp in states_fine:
            db.session.add(samp)
        db.session.commit()
        yield states_fine

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


def test_resample_not_enough_data(app, fake_samples, fake_states):
    samples_ts = Sample.timeseries(fake_samples[-10:])
    states_ts = State.timeseries(fake_states[-2:])
    res_samples, res_states = jointerpolate([samples_ts, states_ts], max_points=10)
    assert 8 < len(samples_ts) < 12
    # There is not enough data to make a reasonable interpolation for states, so we mostly care that this
    # didn't crash and returned something
    assert states_ts is not None

def test_resample_samples_states(app, fake_samples, fake_states):
    samples_ts = Sample.dataframe(fake_samples)
    states_ts = State.dataframe(fake_states)
    res_samples, res_states = jointerpolate([samples_ts, states_ts], max_points=50)
    assert 40 < len(res_samples) < 55
    assert 40 < len(res_states) < 55

    # assert interpolate_multiple yields same results as interpolate_samples_states
    resampled_samples, resampled_states = jointerpolate([samples_ts, states_ts], max_points=50)
    assert 40 < len(resampled_samples) < 55
    assert 40 < len(resampled_states) < 55

def test_resample(app, fake_samples):
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

def test_update_state(app, fake_states):
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

def test_get_states(app, fake_states):
    latest = State.latest()
    assert latest
    assert latest.id == fake_states[-1].id

