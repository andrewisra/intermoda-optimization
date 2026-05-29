from datetime import datetime, timedelta
from src.optimizer.connection_optimizer import optimize_connection


def test_connect():
    now = datetime(2026, 5, 23, 7, 0)
    result = optimize_connection(now, now + timedelta(minutes=5))
    assert result['decision'] == 'connect'


def test_hold_vehicle():
    now = datetime(2026, 5, 23, 7, 0)
    result = optimize_connection(now, now - timedelta(minutes=2))
    assert result['decision'] == 'hold_vehicle'
