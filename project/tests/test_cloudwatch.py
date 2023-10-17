import pytest
from project.api.cloudwatch import create_cron  # Replace 'your_module' with the actual module name


class TestCreateCron:
    def test_create_cron_valid_time(self):
        # Test with valid time and no adjustment
        result = create_cron("12:30", 0)
        assert result == "cron(30 12 * * ? *)"


    def test_create_cron_with_positive_adjustment(self):
        # Test with valid time and positive adjustment
        result = create_cron("12:30", 1)
        assert result == "cron(30 11 * * ? *)"


    def test_create_cron_with_negative_adjustment(self):
        # Test with valid time and negative adjustment
        result = create_cron("12:30", -1)
        assert result == "cron(30 13 * * ? *)"


    def test_create_cron_hour_positive_wraparound(self):
        # Test with time adjustment causing hour to exceed 23
        result = create_cron("23:30", 2)
        assert result == "cron(30 21 * * ? *)"  # This assumes your function handles hour wraparound


    def test_create_cron_hour_negative_wraparound(self):
        # Test with time adjustment causing hour to wrap around to negative
        result = create_cron("01:00", -1)
        assert result == "cron(0 2 * * ? *)"  # This assumes your function handles hour wraparound


    def test_create_cron_invalid_time_format(self):
        # Test with invalid time format
        with pytest.raises(ValueError):
            create_cron("2430", 0)


    def test_create_cron_non_integer_adjustment(self):
        # Test with non-integer time adjustment
        with pytest.raises(TypeError):
            create_cron("12:30", "1")  # Passing string instead of integer

