"""Test all features of website."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple

import pytest
from bs4 import BeautifulSoup
from flask import Flask
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from seleniumbase import BaseCase

from tests.schema import check_config_schema


def any_required_questions(questions: List[Dict[str, Any]]) -> bool:
    """Determines if any questions are required."""
    return any(q["required"] for q in questions)


def read_html_file(file_path: Path) -> str:
    """Open an HTML file and return contents as string."""
    with open(file_path, "r") as file:
        html_content = file.read()
    return html_content


def convert_to_isoformat(
    date: Optional[str] = None,
    time: Optional[str] = None,
    period: Optional[str] = None,
    **kwargs,
) -> str:
    """Converts a datetime-local test input into ISO 8601 format."""
    # Initialize variables for date and time objects
    date_obj = None
    time_obj = None

    # Check for valid input
    if date is None and time is None:
        raise ValueError("Either date or time must be provided")

    # Convert date string to datetime object
    if date is not None:
        date_obj = datetime.strptime(date, "%d%m%Y")

    # Convert time string to datetime object
    if time is not None:
        if period is None:
            raise ValueError("Period (AM/PM) must be provided for time conversion")
        time_str = f"{time} {period}"
        time_obj = datetime.strptime(time_str, "%I%M %p")

    # Determine final string based on date and time presence
    final_str = ""
    if date_obj and time_obj:
        final_str = datetime.combine(date_obj.date(), time_obj.time()).strftime(
            "%Y-%m-%dT%H:%M"
        )
    elif date_obj:
        final_str = date_obj.strftime("%Y-%m-%d")
    elif time_obj:
        final_str = time_obj.strftime("%H:%M")

    return final_str


def select_options(question: Dict[str, Any]) -> str:
    """Chose selection from options."""
    # count number of options NOT disabled
    for option in question["options"]:
        # check if disabled present
        if option.get("disabled", False):
            # skip disabled options
            continue

        else:
            # end
            break

    # get the first valid option
    return option["value"]


def fill_out_form(
    form_element: WebElement, config: Dict[str, Any], form_inputs: Dict[str, Any]
) -> Generator[Tuple[str, str], None, None]:
    """Programmatically fill out form and yield name/value pairs."""
    # loop over questions
    for question in config["questions"]:
        # now get element with name
        input_element = form_element.find_element(By.NAME, question["name"])

        # get tag element type
        tag_name = input_element.tag_name.lower()

        # control flow for different types
        if tag_name == "input" or tag_name == "textarea":
            # get the type
            input_type = input_element.get_attribute("type")

            # check input_type
            assert input_type is not None

            # get test value for input type
            test_value = form_inputs[input_type]

            # check if date/time dict
            if isinstance(test_value, dict):
                # now loop over multiple input steps
                for sub_input in test_value.values():
                    # send it
                    input_element.send_keys(sub_input)

                # now update test value
                test_value = convert_to_isoformat(**test_value)

            else:
                # just normal
                input_element.send_keys(test_value)

            # generate
            yield question["name"], test_value

        elif tag_name == "select":
            # get sample selection from options
            sample_option = select_options(question)

            # find all option elements within the select element
            option_elements = input_element.find_elements(By.TAG_NAME, "option")

            # loop through the option elements and select the desired one
            for option_element in option_elements:
                # basically get first option that is not empty (i.e. a default)
                if option_element.get_attribute("value") == sample_option:
                    # click it ...
                    option_element.click()

            # generate
            yield question["name"], sample_option


def extract_received_form_input(
    response_html: str,
) -> Generator[Tuple[str, str], None, None]:
    """Extract input received from form submission."""
    # parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(response_html, "html.parser")

    # find the container element
    container = soup.find("div", class_="container")

    # find all label elements within the container
    labels = container.find_all("label")

    # iterate over the labels to retrieve the key-value pairs
    for label in labels:
        # get label's "for" attribute as key
        key = label["for"]

        # now get immediate value element
        value_element = label.find_next_sibling("p")

        # clean it
        received_value = value_element.text.strip()

        # yield the key/value pair
        yield key, received_value


@pytest.mark.website
def test_config_schema(default_site_config: Dict[str, Any]) -> None:
    """Check that the given config.json schema is correct."""
    assert check_config_schema(default_site_config), "Check config.json file."


@pytest.mark.website
def test_normal_display(sb: BaseCase, live_session_web_app_url: str) -> None:
    """Simply tests that the website is displaying normally."""
    # open with browser
    sb.open(live_session_web_app_url)

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
    sb: BaseCase, live_session_web_app_url: str, default_site_config: Dict[str, Any]
) -> None:
    """Test that email is dynamically added to instructions."""
    # temp website src
    sb.open(live_session_web_app_url)

    # get instructions text
    instruct_text = sb.get_text("#instructions")

    # check email in text
    assert default_site_config["email"] in instruct_text


@pytest.mark.website
def test_custom_title_works(
    sb: BaseCase, live_session_web_app_url: str, default_site_config: Dict[str, Any]
) -> None:
    """Test that title is dynamically updated from config.json."""
    # temp website src
    sb.open(live_session_web_app_url)

    # get the title of the webpage
    title = sb.get_title()

    # check email in text
    assert default_site_config["title"] == title


@pytest.mark.website
def test_form_backend_updated(
    sb: BaseCase, live_session_web_app_url: str, submit_route: str
) -> None:
    """Check that the form backend url has been updated correctly."""
    # open the webpage
    sb.open(live_session_web_app_url)

    # find the form element
    form_element = sb.get_element("form")

    # make sure it exists
    assert form_element is not None

    # get the value of the "action" attribute of the form element
    form_target = form_element.get_attribute("action")

    # make sure it exists
    assert form_target is not None

    # now check that it is the right url
    assert form_target == live_session_web_app_url + submit_route


@pytest.mark.website
def test_form_submission(
    sb: BaseCase,
    live_session_web_app_url: str,
    form_inputs: Dict[str, Any],
    session_web_app: Flask,
) -> None:
    """Check that the given form upon completion can be succesfully submitted."""
    # get config file
    client = session_web_app.test_client()
    response = client.get("/config.json")

    # convert the response content to JSON
    config = json.loads(response.data)

    # open the webpage
    sb.open(live_session_web_app_url)

    # find the form element
    form_element = sb.get_element("form")

    # fill out form
    submitted_input = {
        k: v for k, v in fill_out_form(form_element, config, form_inputs)
    }

    # get send button ...
    send_button = form_element.find_element(By.ID, "send_button")

    # ... now click it
    send_button.click()

    # check that the form was submitted
    sb.assert_text("Contact Form Response")

    # get the HTML content of the response
    response_html = sb.get_page_source()

    # get received input from Flask response html
    received_input = {k: v for k, v in extract_received_form_input(response_html)}

    # check keys are same
    missing_keys = set(submitted_input) - set(received_input)
    assert not missing_keys, f"Keys are not the same: {missing_keys}"

    # now check values
    for key in submitted_input.keys():
        # get values
        value1 = submitted_input[key]
        value2 = received_input[key]

        # check
        assert (
            value1 == value2
        ), f"Submitted input: {value1} differs from received: {value2}"

    # save screenshot for confirmation
    sb.save_screenshot_to_logs()


@pytest.mark.website
def test_form_required_constraint(
    sb: BaseCase, live_session_web_app_url: str, session_web_app: Flask
) -> None:
    """Check form denies submission if a required question is unanswered."""
    # get config file
    client = session_web_app.test_client()
    response = client.get("/config.json")

    # convert the response content to JSON
    config = json.loads(response.data)

    # open the webpage
    sb.open(live_session_web_app_url)

    # find the form element
    form_element = sb.get_element("form")

    # get send button ...
    send_button = form_element.find_element(By.ID, "send_button")

    # store page source before
    page_source = {"before": sb.get_page_source()}

    # ... now click it
    send_button.click()

    # now store it after
    page_source["after"] = sb.get_page_source()

    # now check appropriate behavior
    if any_required_questions(config["questions"]):
        # should NOT see contact form response
        assert page_source["before"] == page_source["after"]

    else:
        # should see contact form response
        sb.assert_text("Contact Form Response")

    # save screenshot for confirmation
    sb.save_screenshot_to_logs()


@pytest.mark.website
def test_form_download(
    sb: BaseCase,
    live_session_web_app_url: str,
    session_web_app: Flask,
    form_inputs: Dict[str, Any],
) -> None:
    """Check that the given form upon completion can be succesfully downloaded."""
    # get config file
    client = session_web_app.test_client()
    response = client.get("/config.json")

    # convert the response content to JSON
    config = json.loads(response.data)

    # open the webpage
    sb.open(live_session_web_app_url)

    # find the form element
    form_element = sb.get_element("form")

    # fill out form
    submitted_input = {
        k: v for k, v in fill_out_form(form_element, config, form_inputs)
    }

    # get download button ...
    download_button = form_element.find_element(By.ID, "download_button")

    # ... now click it ...
    download_button.click()

    # ... and make sure file is present in downloads dir
    sb.assert_downloaded_file("contact_form_response.html")

    # now get path to downloaded form response
    download_path = sb.get_path_of_downloaded_file("contact_form_response.html")

    # read HTML download file into string
    download_html = read_html_file(sb.get_path_of_downloaded_file(download_path))

    # get received input from Flask response html
    received_input = {k: v for k, v in extract_received_form_input(download_html)}

    # check keys are same
    missing_keys = set(submitted_input) - set(received_input)
    assert not missing_keys, f"Keys are not the same: {missing_keys}"

    # now check values
    for key in submitted_input.keys():
        # get values
        value1 = submitted_input[key]
        value2 = received_input[key]

        # check
        assert (
            value1 == value2
        ), f"Submitted input: {value1} differs from received: {value2}"

    # save screenshot for confirmation
    sb.save_screenshot_to_logs()
