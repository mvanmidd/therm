from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

from therm import app

db = SQLAlchemy(app)


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    time = db.Column(db.DateTime, default=datetime.utcnow)
    temp = db.Column(db.Float)
    pressure = db.Column(db.Float)
    location = db.Column(db.String(20))

    def __repr__(self):
        return "<Sample {} {}: Temp {} Pres {}>".format(self.time.strftime('%Y-%m-%d %H:%M'),
                                                        self.location,
                                                        self.temp,
                                                        self.pressure)
