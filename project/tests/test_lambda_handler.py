import os
import pytest

from lambda_handler import *


def test_handler_calculate():
    # Given
    os.environ["OFFLINE_DEBUG"] = "true"
    event_data = {
        "msg": "calculate",
        "data": ""
        }

    # When
    handler(event_data, None)

    # Then
    assert 1 == 1


def test_handler_update():
    # Given
    os.environ["OFFLINE_DEBUG"] = "true"
    event_data = {
        "msg": "update",
        "data": [
            {
                "from_hours": "05:30",
                "too_hours": "06:00"
            },
            {
                "from_hours": "22:30",
                "too_hours": "23:00"
            }
        ]
    }

    # When
    handler(event_data, None)

    # Then
    assert 1 == 1