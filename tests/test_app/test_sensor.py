import pytest

from therm import mpl115

def test_read(app):
    mpl115.init_app(app)
    temp, humidity = mpl115.read()
    # Random values from mocked GPIO, after decoding and scaling, seem to be in this range.
    assert -200 < temp < 300
