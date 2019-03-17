from datetime import datetime


from flask_sqlalchemy import SQLAlchemy, Model
import pandas as pd
from sqlalchemy.orm.exc import NoResultFound


DEFAULT_LOCATION = None

db = SQLAlchemy()

def interpolate_multiple(ts_list, max_points=50):
    """Interpolate multiple timeseries, using first element to select bounds

    Args:
        ts_list: list of pd.TimeSeries objects to interpolate
        max_points:

    Returns:
        list(pd.Timeseries): resampled timeserieses

    """
    primary = ts_list[0]
    first = primary.index.min()
    last = primary.index.max()
    resampled_list = []
    if first and last and not (pd.isnull(first) or pd.isnull(last)):
        # Only do resampling if we have valid bounds. If no points were found, first and last will be NaN
        secs = int((last - first).total_seconds() // (max_points + 1))
        periodsize = "{:d}S".format(secs)

        for timeseries in ts_list:
            resampled = timeseries.resample(periodsize, how="mean")
            if any(resampled.isnull()):
                resampled = resampled.interpolate("quadratic")
            resampled_list.append(resampled)
        return resampled_list
    else:
        return [Sample.timeseries([]) for _ in resampled_list]

def interpolate_samples_states(samples_ts, states_ts, max_points=50):
    first = samples_ts.index.min()
    last = samples_ts.index.max()
    if first and last and not (pd.isnull(first) or pd.isnull(last)):
        # Only do resampling if we have valid bounds. If no points were found, first and last will be NaN
        secs = int((last - first).total_seconds() // (max_points + 1))
        periodsize = "{:d}S".format(secs)

        resampled_samples = samples_ts.resample(periodsize, how="mean")
        if any(resampled_samples.isnull()):
            resampled_samples = resampled_samples.interpolate("quadratic")
        resampled_states = states_ts.resample(periodsize, how="mean")
        if any(resampled_states.isnull()):
            resampled_states = resampled_states.interpolate("quadratic")
        return resampled_samples, resampled_states
    else:
        return Sample.timeseries([]), State.timeseries([])


class TimeSeriesBase(object):
    """Shared functionality for therm models."""

    DEFAULT_TIMESERIES = None

    @classmethod
    def latest(cls, limit=1, location=None, strict=False):
        """Return most recent row(s)

        Args:
            limit (int): num rows
            location (str): filter by location

        Returns:
            cls: Latest row(s)

        """
        query = cls.query
        if location:
            query = query.filter_by(location=location)
        query = query.order_by(cls.time.desc())
        if limit == 1:
            try:
                return query.first()
            except NoResultFound as e:
                if strict:
                    raise e
                else:
                    return None
        else:
            return list(reversed(query.limit(limit).all()))

    @classmethod
    def since(cls, tmin, tmax=None, limit=10000):
        """

        Args:
            tmin:
            tmax:

        Returns:

        """
        query = cls.query
        query = query.filter(cls.time >= tmin)
        if tmax:
            query = query.filter(cls.time < tmax)
        query = query.order_by(cls.time.asc())
        return query.limit(limit).all()


    def _asdict(self):
        d = {}
        for column in self.__table__.columns:
            d[column.name] = getattr(self, column.name)
        return d

    @classmethod
    def timeseries(cls, rows, attr_name=None):
        """

        Args:
            rows: rows to convert
            attr_name: Attribute to generate timeseries for. default is cls.DEFAULT_TIMESERIES

        Returns:
            ps.Series: timeseries

        """
        attr_name = attr_name or cls.DEFAULT_TIMESERIES
        return pd.Series(data=[getattr(s, attr_name) for s in rows], index=pd.Index(data=[s.time for s in rows], dtype='datetime64[ns]'))



class State(TimeSeriesBase, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    time = db.Column(db.DateTime, default=datetime.utcnow)
    set_point = db.Column(db.Float, nullable=False)
    set_point_enabled = db.Column(db.Boolean, nullable=False, default=False)
    heat_on = db.Column(db.Boolean, nullable=False, default=False)
    location = db.Column(db.String(20), default=DEFAULT_LOCATION)

    DEFAULT_TIMESERIES = "set_point"

    @classmethod
    def refresh(cls):
        """Rewrite the latest state"""
        current_state = cls.latest()
        new_attrs = current_state._asdict()
        new_attrs.pop("id")
        new_attrs.pop("time")
        new_state = cls(**new_attrs)
        db.session.add(new_state)
        db.session.commit()

    @classmethod
    def update_state(cls, attr_name, value):
        """Update the given state attribute to the given value.

        If the given attr_name, value are consistent with the current state, do nothing.

        Else, create a copy of the current state, update attr_name, and insert.

        Returns:
            bool: Whether the state changed
        """
        current_state = cls.latest()
        if getattr(current_state, attr_name) != value:
            new_attrs = current_state._asdict()
            new_attrs.pop("id")
            new_attrs.pop("time")
            new_attrs[attr_name] = value
            new_state = cls(**new_attrs)
            db.session.add(new_state)
            db.session.commit()
            return True
        else:
            return False

    def __repr__(self):
        return "<State {}: Set {}, Set temp {}, Heat on {}>".format(
            self.time.strftime("%Y-%m-%d %H:%M"), self.set_point_enabled, self.set_point, self.heat_on
        )


class Sample(TimeSeriesBase, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    temp = db.Column(db.Float, nullable=False)
    pressure = db.Column(db.Float)
    location = db.Column(db.String(20), default=DEFAULT_LOCATION)

    DEFAULT_TIMESERIES = "temp"

    def __repr__(self):
        return "<Sample {} {}: Temp {} Pres {}>".format(
            self.time.strftime("%Y-%m-%d %H:%M"), self.location, self.temp, self.pressure
        )

class Schedule(db.Model):
    day_of_week = db.Column(db.String(20), primary_key=True)
    time_of_day = db.Column(db.Time, primary_key=True)
    set_point = db.Column(db.Float, nullable=True)

    def next_scheduled(self, as_of=None):
        """Return the next scheduled action.

        Args:
            as_of: Return next scheduled action as of a particular time. If omitted, use datetime.utcnow()

        Returns:
            Schedule: next scheduled action

        """
        raise NotImplementedError()