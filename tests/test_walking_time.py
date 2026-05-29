from src.aits.optimizer.walking_time import estimate_personalized_walking_time


def test_personalized_walking_time_with_consent():
    result = estimate_personalized_walking_time(8, "RELAXED", True, "SHORT")
    assert result.personalized_minutes == 10.0
    assert result.consent_used is True


def test_personalized_walking_time_without_consent():
    result = estimate_personalized_walking_time(8, "ASSISTED", False, "SHORT")
    assert result.personalized_minutes == 8.0
    assert result.consent_used is False
