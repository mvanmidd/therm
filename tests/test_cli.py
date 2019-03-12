import pytest
from pytest_mock import mocker

import therm.cli as cli
from therm.models import db, Sample, State

@pytest.fixture
def mock_buttons(mocker):
    return mocker.patch('{}.buttons'.format(cli.__name__))

@pytest.fixture
def mock_relay(mocker):
    return mocker.patch('{}.relay'.format(cli.__name__))

@pytest.fixture
def mock_mpl115(mocker):
    return mocker.patch('{}.mpl115'.format(cli.__name__))

def test_adjust_temp(mock_buttons, app, fake_state):
    cli._register_buttons()
    mock_buttons.register_on_off.assert_called_once()
    mock_buttons.register_temp_up.assert_called_once()
    mock_buttons.register_temp_down.assert_called_once()

    # Call the up_callback and assert that set point is enabled, and raised by cli.TEMP_INCREMENT from previous
    up_callback, _ = mock_buttons.register_temp_up.call_args
    up_callback = up_callback[0]
    State.update_state('set_point_enabled', False)
    State.update_state('set_point', 72)
    before = State.latest()
    up_callback()
    after = State.latest()
    assert after.set_point == before.set_point + cli.TEMP_INCREMENT
    assert after.set_point_enabled

def test_set_point(mock_mpl115, mock_relay, app, fake_state):
    State.update_state('set_point', 72)
    State.update_state('set_point_enabled', True)
    State.update_state('heat_on', False)
    mock_mpl115.read.return_value = (60, 10)
    cli._poll_once()
    mock_mpl115.read.assert_called_once()
    mock_relay.on.assert_called_once()
    after = State.latest()
    assert after.heat_on

def test_read_write_temp(mock_mpl115, app, fake_state):
    mock_mpl115.read.return_value = (10, 10)
    cli._poll_once()
    mock_mpl115.read.assert_called_once()
    assert Sample.latest().temp == 10


