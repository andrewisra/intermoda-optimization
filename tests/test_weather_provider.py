"""Tests for weather_provider.py — Weather/flood data (synthetic mode)."""
import pytest
from datetime import date, time

from src.aits.data.weather_provider import (
    get_weather_synthetic,
    is_wet_season,
    assign_date,
)


class TestIsWetSeason:
    """Test wet/dry season detection."""

    def test_january_is_wet(self):
        assert is_wet_season(1) is True

    def test_april_is_wet(self):
        assert is_wet_season(4) is True

    def test_october_is_wet(self):
        assert is_wet_season(10) is True

    def test_july_is_dry(self):
        assert is_wet_season(7) is False

    def test_september_is_dry(self):
        assert is_wet_season(9) is False


class TestAssignDate:
    """Test synthetic date assignment for GTFS weather joining."""

    def test_returns_date_object(self):
        result = assign_date(0, [1, 2, 3])  # Monday in Jan-Mar
        assert isinstance(result, date)

    def test_matches_weekday(self):
        result = assign_date(0, [1, 6])  # Monday in Jan or Jun
        assert result.weekday() == 0

    def test_matches_month_range(self):
        result = assign_date(3, [10, 11, 12])  # Thursday in Oct-Dec
        assert result.month in [10, 11, 12]
        assert result.weekday() == 3


class TestGetWeatherSynthetic:
    """Test synthetic weather generation."""

    def test_returns_dict_with_required_keys(self):
        result = get_weather_synthetic(date(2024, 1, 15), time(10, 0))
        assert "rainfall_level" in result
        assert "flood_flag" in result
        assert "temperature_c" in result

    def test_rainfall_level_in_valid_range(self):
        for _ in range(100):
            result = get_weather_synthetic(date(2024, 1, 15), time(10, 0))
            assert result["rainfall_level"] in [0, 1, 2, 3]

    def test_flood_flag_is_binary(self):
        for _ in range(100):
            result = get_weather_synthetic(date(2024, 1, 15), time(10, 0))
            assert result["flood_flag"] in [0, 1]

    def test_temperature_in_jakarta_range(self):
        for _ in range(100):
            result = get_weather_synthetic(date(2024, 7, 15), time(12, 0))
            assert 24 <= result["temperature_c"] <= 35

    def test_wet_season_has_more_rain(self):
        """Wet season should produce more rainfall than dry season."""
        wet_rains = [get_weather_synthetic(date(2024, 1, 15), time(14, 0))["rainfall_level"]
                     for _ in range(500)]
        dry_rains = [get_weather_synthetic(date(2024, 7, 15), time(14, 0))["rainfall_level"]
                     for _ in range(500)]
        assert sum(wet_rains) > sum(dry_rains), "Wet season should have more rain"

    def test_afternoon_has_more_rain(self):
        """Afternoon (14-18) should have more rain than morning."""
        afternoon = [get_weather_synthetic(date(2024, 1, 15), time(15, 0))["rainfall_level"]
                     for _ in range(500)]
        morning = [get_weather_synthetic(date(2024, 1, 15), time(8, 0))["rainfall_level"]
                   for _ in range(500)]
        assert sum(afternoon) > sum(morning), "Afternoon should have more rain"

    def test_flood_correlated_with_heavy_rain(self):
        """Floods should be more likely during heavy rain."""
        heavy_rain_floods = []
        no_rain_floods = []
        for _ in range(1000):
            r = get_weather_synthetic(date(2024, 1, 15), time(14, 0))
            if r["rainfall_level"] == 3:
                heavy_rain_floods.append(r["flood_flag"])
            elif r["rainfall_level"] == 0:
                no_rain_floods.append(r["flood_flag"])
        if heavy_rain_floods and no_rain_floods:
            assert sum(heavy_rain_floods) / len(heavy_rain_floods) > \
                   sum(no_rain_floods) / len(no_rain_floods), \
                   "Heavy rain should have higher flood probability"
