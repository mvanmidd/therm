from therm.models import db, Sample, State

def test_update_state(app, fake_state):
    with app.app_context():
        latest = State.latest()
        State.update_state('set_point_enabled', not latest.set_point_enabled)
        new_state = State.latest()
        assert new_state.set_point_enabled != latest.set_point_enabled
        assert latest
        assert latest.id != new_state.id

def test_get_states(app, fake_state):
    with app.app_context():
        latest = State.latest()
        assert latest
        assert latest.id == fake_state.id

