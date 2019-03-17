from datetime import datetime, timedelta
import pytz

import pandas as pd

from flask import current_app, Blueprint, render_template, jsonify, request

from .models import db, Sample, State, interpolate_samples_states
from .mpl115 import read

root = Blueprint("root", __name__, url_prefix="")

# Maximum points to plot on the on-device (small) chart
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

def datetimefilter(value, format="%I:%M %p"):
    tz = pytz.timezone('US/Eastern') # timezone you want to convert to from UTC
    utc = pytz.timezone('UTC')
    value = utc.localize(value, is_dst=None).astimezone(pytz.utc)
    local_dt = value.astimezone(tz)
    return local_dt.strftime(format)

def _plot_temps(temps, labels, set_points=None):
    """Generate template params for plotting the given temps

    Args:

    Returns:
        dict: params for template

    """
    set_points = set_points or []
    labels = [datetimefilter(s) for s in labels]
    temp_values_fmt = ["{:.2f}".format(s) for s in temps]
    set_points_fmt = ["{:.2f}".format(s) for s in set_points]
    current_app.logger.debug("\nLabels: {}\nValues: {}".format(", ".join(labels), ", ".join(temp_values_fmt)))
    ymin = min([s for s in temps + set_points]) - 1 if temps + set_points else 0
    ymax = max([s for s in temps + set_points]) + 1 if temps + set_points else 100
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


def _get_samples_states(hours = None, num_points = None):
    """

    Args:
        hours (optional[int])
        num_points (optional[int]):

    Returns:
        tuple(pd.Timeseries(Sample), pd.TimeSeries(State)): samples, states

    """
    if not hours and not num_points:
        return [], []
    if hours:
        samples_ts = Sample.timeseries(Sample.since(datetime.utcnow() - timedelta(hours=hours)))
        states_ts = State.timeseries(State.since(datetime.utcnow() - timedelta(hours=hours)))
    elif num_points:
        n = max(num_points, 5)
        samples_ts = Sample.timeseries(Sample.latest(limit=n))
        states_ts = State.timeseries(State.latest(limit=n))
    return samples_ts, states_ts

@root.route("/chart")
def chart():
    """Get a chart of temp and set point

    Request.args:
        n: latest n samples
        hours: latest `hours` hours, default 12
    """
    n = int(request.args.get("n")) if request.args.get("n") else None
    hours = float(request.args.get("hours")) if (request.args.get("hours") and not n) else 12
    samples_ts, states_ts = _get_samples_states(hours=hours, num_points=n)
    resampled_samples, resampled_states = interpolate_samples_states(samples_ts, states_ts, max_points=MAX_GRAPH_POINTS)

    temp_graph_params = _plot_temps(
        list(resampled_samples.data), list(resampled_samples.index), set_points=list(resampled_states.data)
    )
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
    n = int(request.args.get("n")) if request.args.get("n") else None
    hours = float(request.args.get("hours")) if (request.args.get("hours") and not n) else 2
    samples_ts, states_ts = _get_samples_states(hours=hours, num_points=n)
    resampled_samples, resampled_states = interpolate_samples_states(samples_ts, states_ts, max_points=MAX_GRAPH_POINTS)

    temp_graph_params = _plot_temps(
        list(resampled_samples.data), list(resampled_samples.index), set_points=list(resampled_states.data)
    )
    temp_graph_params["inside_temp"] = _get_latest_temp()
    temp_graph_params["set_point"] = _get_set_point()
    temp_graph_params["heat"] = _get_heat()
    return render_template("dashboard.html", **temp_graph_params)

@root.route("/")
def index():
    temp = _get_latest_temp()
    return render_template("chaeron.html", inside_temp=temp)
