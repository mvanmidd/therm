import asyncio
import pytest
import threading

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

def test_adjust_temp(mock_buttons, app, fake_states):
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
    cli.loop.run_until_complete(asyncio.sleep(.1))
    after = State.latest()
    assert after.set_point == before.set_point + cli.TEMP_INCREMENT
    assert after.set_point_enabled

def test_set_point(mock_mpl115, mock_relay, app, fake_states):
    State.update_state('set_point', 72)
    State.update_state('set_point_enabled', True)
    State.update_state('heat_on', False)
    mock_mpl115.read.return_value = (60, 10)
    cli._poll_once()
    mock_mpl115.read.assert_called_once()
    mock_relay.on.assert_called_once()
    after = State.latest()
    assert after.heat_on

def test_read_write_temp(mock_mpl115, app, fake_states):
    mock_mpl115.read.return_value = (10, 10)
    cli._poll_once()
    mock_mpl115.read.assert_called_once()
    assert Sample.latest().temp == 10

def test_thread_safe(mock_buttons, app, fake_states):
    """Test thread safety.

    The callbacks in the GPIO run in their own thread, so they will not have app context. We can't use the GPIO library
    for off-device tests, so to simulate its behavior, we create a fake thread outside of app context to call the button
    callbacks. Assert that the callback provided by cli can safely be called from a thread outside of app context."""
    cli._register_buttons()
    up_callback, _ = mock_buttons.register_temp_up.call_args
    up_callback = up_callback[0]
    button_thread = threading.Thread(target=up_callback)
    State.update_state('set_point_enabled', False)
    State.update_state('set_point', 72)
    before = State.latest()
    button_thread.start()
    cli.loop.run_until_complete(asyncio.sleep(.1))
    button_thread.join()
    after = State.latest()
    assert after.set_point == before.set_point + cli.TEMP_INCREMENT
    assert after.set_point_enabled



