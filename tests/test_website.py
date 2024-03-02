"""Test all features of website."""

from typing import Any
from typing import Dict
from typing import List

from seleniumbase import BaseCase


def check_questions_schema(questions: List[Dict[str, Any]]) -> bool:
    """Loop over list of questions and check schema of each."""
    # loop over questions
    for q in questions:
        # check schema
        match q:
            case {
                "label": label,
                "name": name,
                "type": type_,
                "required": required,
            } if (
                isinstance(label, str)
                and isinstance(name, str)
                and isinstance(type_, str)
                and isinstance(required, bool)
            ):
                # no problems
                pass

            case _:
                # fail immediately
                return False
    # passed
    return True


def test_config_minimum(default_site_config: Dict[str, Any]) -> None:
    """Make sure default config has at least an email and one question."""
    # make sure email exists
    assert "email" in default_site_config, "Email must be present in config.json."

    # make sure value is not empty
    assert isinstance(default_site_config["email"], str), "Email must be a string."

    # make sure questions exist
    assert "questions" in default_site_config, "No questions key in config.json."

    # get questions
    questions = default_site_config["questions"]

    # make sure questions grouped in list
    assert isinstance(questions, list), "Questions must be in a list."

    # make sure at least one question in list
    assert len(questions) >= 1, "Need at least one question to test form."

    # check questions schema correct
    assert check_questions_schema(questions), "Question schema error."


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
