"""Test all features of website."""

from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from seleniumbase import BaseCase


@dataclass
class Question:
    """Defines the question schema for config.json."""

    label: str
    name: str
    type: str
    required: bool


@dataclass
class Config:
    """Defines the schema for config.json."""

    email: str
    title: str
    subject: str
    questions: List[Question]
    form_backend_url: Optional[str] = None


def check_config_schema(config: Dict[str, Any]) -> bool:
    """Check if the config dictionary conforms to the expected schema."""
    try:
        # try to convert the dictionary to a Config object
        _ = Config(**config)
        return True
    except TypeError:
        return False


def test_config_schema(default_site_config: Dict[str, Any]) -> None:
    """Check that the given config.json schema is correct."""
    assert check_config_schema(default_site_config), "Check config.json file."


def test_normal_display(sb: BaseCase, immutable_website_url: str) -> None:
    """Simply tests that the website is displaying normally."""
    # open with browser
    sb.open(immutable_website_url)

    # verify that the container element is visible
    sb.assert_element_visible(".container")

    # verify that the form element is present
    sb.assert_element_present("form#contact-form")

    # verify that the instructions element is present
    sb.assert_element_present("#instructions")

    # save screenshot for confirmation
    sb.save_screenshot_to_logs()


def test_email_in_instructions(
    sb: BaseCase, immutable_website_url: str, default_site_config: Dict[str, Any]
) -> None:
    """Test that email is dynamically added to instructions."""
    # temp website src
    sb.open(immutable_website_url)

    # get instructions text
    instruct_text = sb.get_text("#instructions")

    # check email in text
    assert default_site_config["email"] in instruct_text


def test_custom_title_works(
    sb: BaseCase, immutable_website_url: str, default_site_config: Dict[str, Any]
) -> None:
    """Test that title is dynamically updated from config.json."""
    # temp website src
    sb.open(immutable_website_url)

    # get the title of the webpage
    title = sb.get_title()

    # check email in text
    assert default_site_config["title"] == title
