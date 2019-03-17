import pytest

from therm import mpl115

def test_not_initialized():
    """With no app context, sensor should raise ValueError."""
    with pytest.raises(ValueError):
        mpl115.read()
