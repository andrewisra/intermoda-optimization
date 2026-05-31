"""Tests for delay_generator.py — Calibrated synthetic delay generation."""
import pytest
import random

from src.aits.data.delay_generator import (
    generate_delay,
    get_incident_rate,
)


class TestGetIncidentRate:
    """Test historical incident rate lookup."""

    def test_busway_low_rate(self):
        rate = get_incident_rate("TRANSJAKARTA", 12, 0)
        assert 0.01 <= rate <= 0.10

    def test_mikrotrans_higher_rate(self):
        rate_busway = get_incident_rate("TRANSJAKARTA", 12, 0)
        rate_mikro = get_incident_rate("MIKROTRANS", 12, 0)
        assert rate_mikro > rate_busway

    def test_rush_hour_higher_rate(self):
        rate_rush = get_incident_rate("TRANSJAKARTA", 8, 0)
        rate_off = get_incident_rate("TRANSJAKARTA", 12, 0)
        assert rate_rush > rate_off

    def test_rain_increases_rate(self):
        rate_dry = get_incident_rate("TRANSJAKARTA", 12, 0)
        rate_rain = get_incident_rate("TRANSJAKARTA", 12, 3)
        assert rate_rain > rate_dry

    def test_rate_always_between_0_and_1(self):
        for mode in ["TRANSJAKARTA", "MIKROTRANS", "MRT_LRT", "KRL"]:
            for hour in [6, 8, 12, 17, 22]:
                for rain in [0, 1, 2, 3]:
                    rate = get_incident_rate(mode, hour, rain)
                    assert 0.0 <= rate <= 1.0, f"Rate {rate} out of range for {mode}/{hour}/{rain}"


class TestGenerateDelay:
    """Test synthetic delay generation."""

    def test_returns_non_negative(self):
        for _ in range(500):
            delay = generate_delay(300, "TRANSJAKARTA", 12, 0, 0)
            assert delay >= 0, f"Negative delay: {delay}"

    def test_returns_float(self):
        delay = generate_delay(300, "TRANSJAKARTA", 12, 0, 0)
        assert isinstance(delay, float)

    def test_busway_has_less_delay_than_mikrotrans(self):
        """Busway with dedicated lane should have less delay."""
        random.seed(42)
        busway_delays = [generate_delay(600, "TRANSJAKARTA", 8, 0, 0) for _ in range(200)]
        random.seed(42)
        mikro_delays = [generate_delay(600, "MIKROTRANS", 8, 0, 0) for _ in range(200)]
        assert sum(busway_delays) < sum(mikro_delays)

    def test_rush_hour_more_delay(self):
        """Rush hour should produce more delay than off-peak."""
        random.seed(42)
        rush_delays = [generate_delay(600, "TRANSJAKARTA", 8, 0, 0) for _ in range(200)]
        random.seed(42)
        off_delays = [generate_delay(600, "TRANSJAKARTA", 12, 0, 0) for _ in range(200)]
        assert sum(rush_delays) > sum(off_delays)

    def test_heavy_rain_more_delay(self):
        """Heavy rain should produce more delay than no rain."""
        random.seed(42)
        rain_delays = [generate_delay(600, "TRANSJAKARTA", 12, 3, 0) for _ in range(200)]
        random.seed(42)
        dry_delays = [generate_delay(600, "TRANSJAKARTA", 12, 0, 0) for _ in range(200)]
        assert sum(rain_delays) > sum(dry_delays)

    def test_flood_causes_large_delay(self):
        """Flood should cause significantly more delay."""
        random.seed(42)
        flood_delays = [generate_delay(600, "TRANSJAKARTA", 12, 0, 1) for _ in range(200)]
        random.seed(42)
        no_flood_delays = [generate_delay(600, "TRANSJAKARTA", 12, 0, 0) for _ in range(200)]
        assert sum(flood_delays) > sum(no_flood_delays)

    def test_longer_segments_have_more_delay(self):
        """Longer segments should generally have more base delay."""
        random.seed(42)
        short_delays = [generate_delay(120, "TRANSJAKARTA", 12, 0, 0) for _ in range(200)]
        random.seed(42)
        long_delays = [generate_delay(900, "TRANSJAKARTA", 12, 0, 0) for _ in range(200)]
        assert sum(long_delays) > sum(short_delays)

    def test_delay_within_reasonable_bounds(self):
        """Delay should generally be under 15 minutes (clip threshold)."""
        for _ in range(200):
            delay = generate_delay(600, "TRANSJAKARTA", 8, 3, 1)
            assert delay <= 20, f"Unreasonably large delay: {delay}"

    def test_delay_distribution_has_variance(self):
        """Multiple calls should produce different delays (noise)."""
        delays = [generate_delay(600, "TRANSJAKARTA", 12, 0, 0) for _ in range(100)]
        assert len(set(delays)) > 50, "Delays should have variance"
