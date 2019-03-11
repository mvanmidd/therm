from flask import current_app, Blueprint, render_template, jsonify

from .models import db, Sample, State
from .mpl115 import read

root = Blueprint("root", __name__, url_prefix="")


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


def _plot_temps(samples):
    """Generate template params for plotting the given temps

    Args:
        temps (list[Sample]): Latest temp samples in sequential order

    Returns:
        dict: params for template

    """
    labels = [s.time.strftime("%H:%M") for s in samples]
    values = ["{:.2f}".format(s.temp) for s in samples]
    inside_temp = samples[-1].temp
    current_app.logger.debug("\nLabels: {}\nValues: {}".format(", ".join(labels), ", ".join(values)))
    ymin = min([s.temp for s in samples]) - 4
    ymax = max([s.temp for s in samples]) + 4
    return {"labels": labels, "values": values, "inside_temp": inside_temp, "y_min": ymin, "y_max": ymax}

def _get_set_point():
    state = State.latest()
    if state and state.set_point_enabled:
        return state.set_point
    else:
        return "off"

@root.route("/chart")
def chart():
    latest_samples = list(reversed(Sample.latest(limit=20)))
    temp_graph_params = _plot_temps(latest_samples)
    temp_graph_params['set_point'] = _get_set_point()
    return render_template("chart.html", **temp_graph_params)


@root.route("/")
def index():
    temp, pres = read()
    current_app.logger.warning("sample message")
    return render_template("chaeron.html", inside_temp=temp)
