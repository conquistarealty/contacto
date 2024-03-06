"""Test all features of website."""

from typing import Any
from typing import Dict

import pytest
from seleniumbase import BaseCase

from tests.schema import check_config_schema


@pytest.mark.website
def test_config_schema(default_site_config: Dict[str, Any]) -> None:
    """Check that the given config.json schema is correct."""
    assert check_config_schema(default_site_config), "Check config.json file."


@pytest.mark.website
def test_normal_display(sb: BaseCase, live_project_web_app_url: str) -> None:
    """Simply tests that the website is displaying normally."""
    # open with browser
    sb.open(live_project_web_app_url)

    # verify that the container element is visible
    sb.assert_element_visible(".container")

    # verify that the form element is present
    sb.assert_element_present("form#contact-form")

    # verify that the instructions element is present
    sb.assert_element_present("#instructions")

    # save screenshot for confirmation
    sb.save_screenshot_to_logs()


@pytest.mark.website
def test_email_in_instructions(
    sb: BaseCase, live_project_web_app_url: str, default_site_config: Dict[str, Any]
) -> None:
    """Test that email is dynamically added to instructions."""
    # temp website src
    sb.open(live_project_web_app_url)

    # get instructions text
    instruct_text = sb.get_text("#instructions")

    # check email in text
    assert default_site_config["email"] in instruct_text


@pytest.mark.website
def test_custom_title_works(
    sb: BaseCase, live_project_web_app_url: str, default_site_config: Dict[str, Any]
) -> None:
    """Test that title is dynamically updated from config.json."""
    # temp website src
    sb.open(live_project_web_app_url)

    # get the title of the webpage
    title = sb.get_title()

    # check email in text
    assert default_site_config["title"] == title
