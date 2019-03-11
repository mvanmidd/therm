from datetime import datetime
from flask_sqlalchemy import SQLAlchemy, Model
from sqlalchemy.orm.exc import NoResultFound


DEFAULT_LOCATION = None


class Base(Model):
    """Shared functionality for therm models."""

    @classmethod
    def latest(cls, limit=1, location=None, strict=False):
        """Return most recent row(s)

        Args:
            limit (int): num rows
            location (str): filter by location

        Returns:
            Base or list[Base]

        """
        """Return latest sample, optionally filtered by location."""
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
            return query.limit(limit).all()

    def _asdict(self):
        d = {}
        for column in self.__table__.columns:
            d[column.name] = getattr(self, column.name)
        return d


db = SQLAlchemy(model_class=Base)


class State(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    time = db.Column(db.DateTime, default=datetime.utcnow)
    set_point = db.Column(db.Float, nullable=False)
    set_point_enabled = db.Column(db.Boolean, nullable=False, default=False)
    heat_on = db.Column(db.Boolean, nullable=False, default=False)
    location = db.Column(db.String(20), default=DEFAULT_LOCATION)
    # latest_samples = db.relationship("Sample", backref="state", lazy=True)

    @classmethod
    def update_state(cls, attr_name, value):
        """Update the given state attribute to the given value.

        If the given attr_name, value are consistent with the current state, do nothing.

        Else, create a copy of the current state, update attr_name, and insert.
        """
        current_state = cls.latest()
        if getattr(current_state, attr_name) != value:
            new_attrs = current_state._asdict()
            new_attrs.pop('id')
            new_attrs.pop('time')
            new_attrs[attr_name] = value
            new_state = cls(**new_attrs)
            db.session.add(new_state)
            db.session.commit()



class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    temp = db.Column(db.Float, nullable=False)
    pressure = db.Column(db.Float)
    location = db.Column(db.String(20), default=DEFAULT_LOCATION)
    # state_id = db.Column(db.Integer, db.ForeignKey("state.id"), nullable=True)

    def __repr__(self):
        return "<Sample {} {}: Temp {} Pres {}>".format(
            self.time.strftime("%Y-%m-%d %H:%M"), self.location, self.temp, self.pressure
        )
