"""Test the fixtures used in the tests."""

import json
from pathlib import Path
from typing import Tuple

import pytest
from flask import Flask
from seleniumbase import BaseCase

from tests.conftest import load_config_file


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
