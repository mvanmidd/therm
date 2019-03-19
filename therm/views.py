from datetime import datetime, timedelta
import pytz

import pandas as pd
import numpy as np

from flask import current_app, Blueprint, render_template, jsonify, request

from .models import db, Sample, State, jointerpolate

root = Blueprint("root", __name__, url_prefix="")

# Maximum points to plot on the on-device (small) chart
MAX_GRAPH_POINTS = 60


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


def datetimefilter(value, format="%I:%M %p"):
    tz = pytz.timezone("US/Eastern")  # timezone you want to convert to from UTC
    utc = pytz.timezone("UTC")
    value = utc.localize(value, is_dst=None).astimezone(pytz.utc)
    local_dt = value.astimezone(tz)
    return local_dt.strftime(format)


def _plot_temps_states(temps, states):
    """Generate template params for plotting the given temps

    Args:

    Returns:
        dict: params for template

    """
    temp_values = [t if not np.isnan(t) else None for t in temps.temp] if len(temps) > 0 else list()
    on_sets = states.apply(
        lambda state: state.set_point if state.set_point_enabled and state.heat_on else np.nan, axis=1
    )
    on_sets = np.where(np.isnan(on_sets), None, on_sets)
    off_sets = list(
        states.apply(
            lambda state: state.set_point if state.set_point_enabled and not state.heat_on else np.nan, axis=1
        )
    )
    off_sets = np.where(np.isnan(off_sets), None, off_sets)
    if len(temp_values) > 0:
        labels = [datetimefilter(s) for s in temps.index]
    else:
        labels = []
    # current_app.logger.debug("\nLabels: {}\nValues: {}".format(", ".join(labels), ", ".join(temp_values_fmt)))
    ymin = np.min(temps.temp) - 4 if len(temps) > 1 else 0
    ymax = np.max(temps.temp) + 4 if len(temps) > 1 else 100
    # ymax = max([s for s in temp_values + on_sets + [100]]) + 1
    return {
        "labels": labels,
        "temp_values": temp_values,
        "set_points_heaton": on_sets,
        "set_points_heatoff": off_sets,
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
    hours = float(request.args.get("hours")) if request.args.get("hours") else 12
    samples_df = Sample.dataframe(Sample.since(datetime.utcnow() - timedelta(hours=hours)))
    states_df = State.dataframe(State.since(datetime.utcnow() - timedelta(hours=hours)))
    resampled_samples, resampled_states = jointerpolate([samples_df, states_df], max_points=MAX_GRAPH_POINTS)
    temp_graph_params = _plot_temps_states(resampled_samples, resampled_states)
    temp_graph_params["inside_temp"] = _get_latest_temp()
    temp_graph_params["set_point"] = _get_set_point()
    temp_graph_params["heat"] = _get_heat()
    return render_template("chart.html", **temp_graph_params)


@root.route("/setpt-up", methods=["POST"])
def setpt_up():
    latest = State.latest()
    State.update_state("set_point_enabled", True)
    State.update_state("set_point", latest.set_point + 0.5)
    return jsonify(State.latest()._asdict()), 200


@root.route("/setpt-off", methods=["POST"])
def setpt_off():
    latest = State.latest()
    State.update_state("set_point_enabled", False)
    return jsonify(State.latest()._asdict()), 200


@root.route("/setpt-down", methods=["POST"])
def setpt_down():
    latest = State.latest()
    State.update_state("set_point_enabled", True)
    State.update_state("set_point", latest.set_point - 0.5)
    return jsonify(State.latest()._asdict()), 200


@root.route("/dashboard")
def dashboard():
    hours = float(request.args.get("hours")) if request.args.get("hours") else 12
    samples_df = Sample.dataframe(Sample.since(datetime.utcnow() - timedelta(hours=hours)))
    states_df = State.dataframe(State.since(datetime.utcnow() - timedelta(hours=hours)))
    resampled_samples, resampled_states = jointerpolate([samples_df, states_df], max_points=MAX_GRAPH_POINTS)
    temp_graph_params = _plot_temps_states(resampled_samples, resampled_states)

    temp_graph_params["inside_temp"] = _get_latest_temp()
    temp_graph_params["set_point"] = _get_set_point()
    temp_graph_params["heat"] = _get_heat()
    return render_template("dashboard.html", **temp_graph_params)


@root.route("/")
def index():
    temp = _get_latest_temp()
    return render_template("chaeron.html", inside_temp=temp)
