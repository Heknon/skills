import time

import pytest

from app.net import ping


@pytest.mark.slow
def test_ping_many_times():
    for _ in range(3):
        time.sleep(0.1)
        assert ping() == "pong"
