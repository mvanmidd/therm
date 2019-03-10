from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    time = db.Column(db.DateTime, default=datetime.utcnow)
    temp = db.Column(db.Float)
    pressure = db.Column(db.Float)
    location = db.Column(db.String(20))

    def _asdict(self):
        d = {}
        for column in Sample.__table__.columns:
            d[column.name] = str(getattr(self, column.name))
        return d

    def __repr__(self):
        return "<Sample {} {}: Temp {} Pres {}>".format(self.time.strftime('%Y-%m-%d %H:%M'),
                                                        self.location,
                                                        self.temp,
                                                        self.pressure)

