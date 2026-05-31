from src.aits.optimizer.risk import calculate_missed_connection_risk


def test_low_risk_connection():
    risk = calculate_missed_connection_risk(5, "LOW", 0.9, 5)
    assert risk["risk_level"] == "LOW"


def test_high_risk_missed_connection():
    risk = calculate_missed_connection_risk(-2, "HIGH", 0.6, -2)
    assert risk["risk_level"] == "HIGH"
