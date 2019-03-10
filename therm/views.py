from flask import render_template

from therm import app
from .mpl115 import read

LOG = app.logger


@app.route("/")
def index():
    temp, pres = read()
    LOG.warning("sample message")
    return render_template("chaeron.html", inside_temp=temp)
