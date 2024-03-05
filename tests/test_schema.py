"""Test the schemas of the various config.json section."""

from typing import Dict
from typing import Generator
from typing import Tuple
from typing import Union

import pytest

from tests.schema import SelectBoxOptions


def selectbox_option_test_data() -> (
    Generator[Tuple[Dict[str, Union[bool, str]], bool], None, None]
):
    """Generates all possible test data for testing selectbox options schema."""
    # valid selectbox option
    yield {
        "label": "Option 1",
        "value": "option1",
        "selected": True,
        "disabled": False,
    }, True

    # valid selectbox option with defaults
    yield {"label": "Option 2", "value": "option2"}, True

    # invalid selectbox option: wrong field types
    yield {"label": "Option 3", "value": "option3", "selected": "true"}, False
    yield {"label": "Option 4", "value": "option4", "disabled": "false"}, False

    # invalid selectbox option: missing required keys
    yield {"label": "Option 5"}, False
    yield {"value": "option6"}, False

    # invalid selectbox option: wrong key name
    yield {"label": "Option 7", "val": "option7"}, False
    yield {
        "label": "Option 8",
        "value": "option8",
        "selected": True,
        "disbled": False,
    }, False


@pytest.mark.schema
@pytest.mark.parametrize("option_data, expected_result", selectbox_option_test_data())
def test_selectbox_option(option_data, expected_result) -> None:
    """Tests that every selectbox option conforms to expected result."""
    try:
        option = SelectBoxOptions(**option_data)
        assert option is not None
        assert (option.label == option_data["label"]) == expected_result
    except (TypeError, ValueError):
        assert not expected_result
