
from flask import current_app, Blueprint, render_template, jsonify

from .models import db, Sample
from .mpl115 import read

root = Blueprint('root', __name__, url_prefix='')

@root.route("/samples")
def samples():
    res = Sample.query.all()
    # import pdb; pdb.set_trace()
    return jsonify([r._asdict() for r in res])




@root.route("/")
def index():
    temp, pres = read()
    current_app.logger.warning("sample message")
    return render_template("chaeron.html", inside_temp=temp)
