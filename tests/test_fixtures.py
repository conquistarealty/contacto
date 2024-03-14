"""Test the fixtures used in the tests."""

import json
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Tuple

import pytest
from bs4 import BeautifulSoup
from flask import Flask
from seleniumbase import BaseCase

from tests.conftest import load_config_file
from tests.schema import check_config_schema


def check_files_subset(source_dir: Path, webfiles: Tuple[str, ...]) -> bool:
    """Check if subset of files is found in another directory."""
    # create sets
    source_dir_set = set([str(entry.name) for entry in source_dir.iterdir()])
    webfiles_set = set(webfiles)

    # check subset
    return webfiles_set.issubset(source_dir_set)


@pytest.mark.fixture
def test_websrc_in_project_dir(
    project_directory: Path, website_files: Tuple[str, ...]
) -> None:
    """Simply confirm that the website files are in the project dir path."""
    assert check_files_subset(project_directory, website_files)


@pytest.mark.fixture
def test_websrc_in_temp_dir(
    session_websrc_tmp_dir: Path, website_files: Tuple[str, ...]
) -> None:
    """Simply confirm that the website files are in the temp web source dir."""
    assert check_files_subset(session_websrc_tmp_dir, website_files)


@pytest.mark.fixture
def test_config_keys_in_form_inputs(
    default_site_config: Dict[str, Any], form_inputs: Dict[str, Any]
) -> None:
    """Check that keys from config.json are present in form input testing fixture."""
    # get types from questions section of config.json
    question_types = [q["type"] for q in default_site_config["questions"]]

    # check config question types missing form inputs (if any)
    missing_keys = set(question_types) - set(form_inputs)

    # no missing keys
    assert (
        not missing_keys
    ), f"Keys found in config.json are absent from test inputs : {missing_keys}"


@pytest.mark.fixture
def test_hello_world_sb(sb: BaseCase, sb_test_url: str) -> None:
    """Just test if SeleniumBase can work on hello world example from docs."""
    # open the browser to the login example page
    sb.open(sb_test_url)

    # type the username/password and mfa code
    sb.type("#username", "demo_user")
    sb.type("#password", "secret_pass")
    sb.enter_mfa_code("#totpcode", "GAXG2MTEOR3DMMDG")  # 6-digit

    # check that login succeeded
    sb.assert_element("img#image1")
    sb.assert_exact_text("Welcome!", "h1")
    sb.click('a:contains("This Page")')

    # save screenshot for confirmation
    sb.save_screenshot_to_logs()


@pytest.mark.flask
@pytest.mark.fixture
def test_index_route(session_web_app: Flask) -> None:
    """Test the index route."""
    client = session_web_app.test_client()
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.flask
@pytest.mark.fixture
def test_other_root_files_route(session_web_app: Flask) -> None:
    """Test the route for serving other root files."""
    client = session_web_app.test_client()
    response = client.get("/config.json")
    assert response.status_code == 200


@pytest.mark.flask
@pytest.mark.fixture
def test_serve_styles_route(session_web_app: Flask) -> None:
    """Test the route for serving CSS files."""
    client = session_web_app.test_client()
    response = client.get("/styles/form.css")
    assert response.status_code == 200


@pytest.mark.flask
@pytest.mark.fixture
def test_serve_scripts_route(session_web_app: Flask) -> None:
    """Test the route for serving JavaScript files."""
    client = session_web_app.test_client()
    response = client.get("/scripts/form.js")
    assert response.status_code == 200


@pytest.mark.flask
@pytest.mark.fixture
def test_submit_form_route(
    session_web_app: Flask,
    submit_route: str,
    dummy_form_post_data: Dict[str, Any],
    dummy_txt_file_data_url: str,
) -> None:
    """Test the route for submitting a form."""
    # get client
    client = session_web_app.test_client()

    # submit response
    response = client.post(
        submit_route, data=dummy_form_post_data, content_type="multipart/form-data"
    )

    # assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # get content
    content = response.data.decode("utf-8")

    # check response html header
    assert "Contact Form Response" in content

    # parse the HTML response
    soup = BeautifulSoup(response.data, "html.parser")

    # find the container div
    container = soup.find("div", class_="container")
    assert container is not None, "Container div not found in HTML response"

    # find and extract form data from the HTML
    form_data = {}
    labels = container.find_all("label")
    for label in labels:
        key = label["for"]
        # find the <p> tag associated with the label
        p_tag = label.find_next_sibling("p")
        if p_tag:
            # find the <a> tag within the <p> tag
            a_tag = p_tag.find("a")
            if a_tag:
                # extract the value of the "href" attribute from the <a> tag
                value = a_tag.get("href")
            else:
                # if <a> tag is not found, set value to None
                value = " ".join(p_tag.stripped_strings)
            form_data[key] = value

    # define expected form data
    expected_form_data = {
        "name": dummy_form_post_data["name"],
        "email": dummy_form_post_data["email"],
        "message": dummy_form_post_data["message"],
        "text_file": dummy_txt_file_data_url,
    }

    # assert that the form data matches the expected form data
    for key in expected_form_data:
        assert (
            form_data[key] == expected_form_data[key]
        ), "Form data in HTML response does not match expected form data"


@pytest.mark.flask
@pytest.mark.fixture
def test_port_in_app_config(session_web_app: Flask) -> None:
    """Confirm port has been set in Flask app config."""
    assert "PORT" in session_web_app.config, "PORT key not set"


@pytest.mark.flask
@pytest.mark.fixture
def test_session_config_form_backend_updated(
    session_websrc_tmp_dir: Path, session_web_app: Flask
) -> None:
    """Make sure config file has been updated with url."""
    # load config file
    config = load_config_file(session_websrc_tmp_dir)

    # get config
    client = session_web_app.test_client()
    response = client.get("/config.json")

    # verify the response status code
    assert response.status_code == 200

    # convert the response content to JSON
    json_data = json.loads(response.data)

    # check that key is in config
    key = "form_backend_url"
    assert key in json_data
    assert key in config

    # check configs match
    assert config[key] == json_data[key]


@pytest.mark.fixture
def test_multi_options_config_schema(
    multiple_select_options_config: Dict[str, Any]
) -> None:
    """Check that the given config.json schema for multi select options is correct."""
    assert check_config_schema(
        multiple_select_options_config
    ), "Error in multi options config fixture."


@pytest.mark.fixture
def test_multi_opts_config_multiple(
    multiple_select_options_config: Dict[str, Any]
) -> None:
    """Confirm that the multi selection options config has multiple options."""
    # get questions
    question = multiple_select_options_config["questions"][0]

    # check multiple options
    assert len(question["options"]) > 1

    # check custom.multiple attr set
    assert question["custom"]["multiple"]


@pytest.mark.fixture
def test_multi_opts_config_defaults(
    multiple_select_options_config: Dict[str, Any]
) -> None:
    """Check that at least one options is selected and disabled."""
    # get options
    options = multiple_select_options_config["questions"][0]["options"]

    # results store
    results = []

    # loop over options
    for opt in options:
        # check for default
        results.append(opt.get("selected", False) and opt.get("disabled", False))

    # now check results
    assert any(results)
