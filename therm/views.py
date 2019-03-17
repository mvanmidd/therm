from datetime import datetime, timedelta

import pandas as pd

from flask import current_app, Blueprint, render_template, jsonify, request

from .models import db, Sample, State
from .mpl115 import read

root = Blueprint("root", __name__, url_prefix="")

MAX_GRAPH_POINTS = 30


@root.route("/samples/latest")
def latest_sample():
    res = Sample.latest()
    return jsonify(res._asdict())


@root.route("/samples")
def samples():
    res = Sample.query.all()
    return jsonify([r._asdict() for r in res])


@root.route("/states/latest")
def latest_state():
    res = State.latest()
    if res:
        return jsonify(res._asdict())
    else:
        return jsonify({})


@root.route("/states")
def states():
    res = State.query.all()
    return jsonify([r._asdict() for r in res])


def interpolate(ts, datetime_index):
    x = pd.concat([ts, pd.Series(index=datetime_index)])
    return x.groupby(x.index).first().sort_index().fillna(method="ffill")[datetime_index]


def _plot_temps(temps, labels, set_points=None):
    """Generate template params for plotting the given temps

    Args:

    Returns:
        dict: params for template

    """
    set_points = set_points or []
    labels = [s.strftime("%H:%M") for s in labels]
    temp_values_fmt = ["{:.2f}".format(s) for s in temps]
    set_points_fmt = ["{:.2f}".format(s) for s in set_points]
    current_app.logger.debug("\nLabels: {}\nValues: {}".format(", ".join(labels), ", ".join(temp_values_fmt)))
    ymin = min([s for s in temps + set_points]) - 1
    ymax = max([s for s in temps + set_points]) + 1
    return {
        "labels": labels,
        "temp_values": temp_values_fmt,
        "set_points_heaton": set_points_fmt,
        "set_points_heatoff": set_points_fmt,
        "y_min": ymin,
        "y_max": ymax,
    }


def _get_latest_temp():
    samp = Sample.latest()
    if samp and samp.temp:
        return samp.temp
    else:
        return 0


def _get_set_point():
    state = State.latest()
    if state and state.set_point_enabled:
        return state.set_point
    else:
        return "off"


def _get_heat():
    state = State.latest()
    return "On" if state.heat_on else "Off"


@root.route("/chart")
def chart():
    """Get a chart of temp and set point

    Request.args:
        n: latest n samples
        hours: latest `hours` hours, default 12
    """
    hours = request.args.get("hours", 12)
    n = request.args.get("n")

    if not n:
        hours = float(hours)
        samples_ts = Sample.timeseries(Sample.since(datetime.utcnow() - timedelta(hours=hours)))
        states_ts = State.timeseries(State.since(datetime.utcnow() - timedelta(hours=hours)))
    else:
        n = int(n)
        # Need at least 5 points for smoothing to work, and we might as well be permissive here
        if n < 5:
            n = 5
        samples_ts = Sample.timeseries(Sample.latest(limit=n))
        states_ts = State.timeseries(State.latest(limit=n))

    first = samples_ts.index.min()
    last = samples_ts.index.max()
    if first and last and not (pd.isnull(first) or pd.isnull(last)):
        # Only do resampling if we have valid bounds. If no points were found, first and last will be NaN
        secs = int((last - first).total_seconds() // (MAX_GRAPH_POINTS + 1))
        periodsize = "{:d}S".format(secs)

        resampled_samples = samples_ts.resample(periodsize, how="mean")
        if any(resampled_samples.isnull()):
            current_app.logger.info("interpolating samples")
            resampled_samples = resampled_samples.interpolate("quadratic")
        resampled_states = states_ts.resample(periodsize, how="mean")
        if any(resampled_states.isnull()):
            current_app.logger.info("interpolating states")
            resampled_states = resampled_states.interpolate("quadratic")

        temp_graph_params = _plot_temps(
            list(resampled_samples.data), list(resampled_samples.index), set_points=list(resampled_states.data)
        )
    else:
        temp_graph_params = {}
    temp_graph_params["inside_temp"] = _get_latest_temp()
    temp_graph_params["set_point"] = _get_set_point()
    temp_graph_params["heat"] = _get_heat()
    return render_template("chart.html", **temp_graph_params)

@root.route('/setpt-up', methods=['POST'])
def setpt_up():
    latest = State.latest()
    State.update_state('set_point_enabled', True)
    State.update_state('set_point', latest.set_point + .5)
    return jsonify(State.latest()._asdict()), 200

@root.route('/setpt-off', methods=['POST'])
def setpt_off():
    latest = State.latest()
    State.update_state('set_point_enabled', False)
    return jsonify(State.latest()._asdict()), 200

@root.route('/setpt-down', methods=['POST'])
def setpt_down():
    latest = State.latest()
    State.update_state('set_point_enabled', True)
    State.update_state('set_point', latest.set_point - .5)
    return jsonify(State.latest()._asdict()), 200


@root.route("/dashboard")
def dashboard():
    temp = _get_latest_temp()
    set_pt = _get_set_point()
    return render_template("dashboard.html", inside_temp=temp, set_point=set_pt)

@root.route("/")
def index():
    temp = _get_latest_temp()
    return render_template("chaeron.html", inside_temp=temp)
