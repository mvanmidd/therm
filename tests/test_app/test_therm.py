from therm.models import State

def test_get_states(client, fake_state):
    response = client.get("/states")
    assert response.status_code == 200
    assert response.get_json() is not None


def test_get_latest_state(client, fake_state):
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

def test_set_pt_up(client, app, fake_state):
    with app.app_context():
        before = State.latest()
        response = client.post("/setpt-up")
        after = State.latest()
        assert response.status_code == 200
        assert response.get_json() is not None
        assert after.set_point == before.set_point + .5
        assert response.get_json()['set_point'] == before.set_point + .5


def test_get_chart_n(client, fake_samples, fake_state):
    response = client.get("/chart?n=10")
    assert response.status_code == 200

def test_get_chart_hours(client, fake_samples, fake_state):
    response = client.get("/chart?hours=.1")
    assert response.status_code == 200

def test_get_chart_default(client, fake_samples, fake_state):
    response = client.get("/chart")
    assert response.status_code == 200


def test_get_main(client):
    rv = client.get("/")
    assert "Temp: " in rv.data.decode()
