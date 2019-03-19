import pandas as pd

from therm.models import State, Sample
from therm.views import _plot_temps_states


def test_get_states(client, fake_states):
    response = client.get("/states")
    assert response.status_code == 200
    assert response.get_json() is not None


def test_get_latest_state(client, fake_states):
    response = client.get("/states/latest")
    assert response.status_code == 200
    assert response.get_json() is not None


def test_get_samples(client, fake_samples):
    results = client.get("/samples").get_json()
    assert len(results) == len(fake_samples)


def test_get_latest_sample(client, fake_samples):
    response = client.get("/samples/latest")
    assert response.status_code == 200
    assert response.get_json() is not None


def test_set_pt_up(client, app, fake_states):
    with app.app_context():
        before = State.latest()
        response = client.post("/setpt-up")
        after = State.latest()
        assert response.status_code == 200
        assert response.get_json() is not None
        assert after.set_point == before.set_point + 0.5
        assert response.get_json()["set_point"] == before.set_point + 0.5


def test_plot_nonempty(client, fake_samples, fake_states):
    params = _plot_temps_states(Sample.dataframe(fake_samples), State.dataframe(fake_states))
    assert len(params["temp_values"]) > 0
    assert len(params["set_points_heaton"]) + len(params["set_points_heatoff"]) > 0


def test_plot_empty(client, fake_samples, fake_states):
    params = _plot_temps_states(pd.DataFrame(data=[]), pd.DataFrame(data=[]))


def test_get_chart_hours(client, fake_samples, fake_states):
    response = client.get("/chart?hours=.1")
    assert response.status_code == 200


def test_get_chart_default(client, fake_samples, fake_states):
    response = client.get("/chart")
    assert response.status_code == 200


def test_get_dashboard_default(client, fake_samples, fake_states):
    response = client.get("/dashboard")
    assert response.status_code == 200


def test_get_main(client):
    rv = client.get("/")
    assert "Temp: " in rv.data.decode()
