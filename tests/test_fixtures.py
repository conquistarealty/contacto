"""Test the fixtures used in the tests."""

from pathlib import Path
from typing import Tuple

import pytest
from seleniumbase import BaseCase


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
def test_websrc_in_temp_dir(temp_web_src: Path, website_files: Tuple[str, ...]) -> None:
    """Simply confirm that the website files are in the temp web source dir."""
    assert check_files_subset(temp_web_src, website_files)


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
def test_index_route(project_web_app):
    """Test the index route."""
    client = project_web_app.test_client()
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.flask
@pytest.mark.fixture
def test_other_root_files_route(project_web_app):
    """Test the route for serving other root files."""
    client = project_web_app.test_client()
    response = client.get("/config.json")
    assert response.status_code == 200


@pytest.mark.flask
@pytest.mark.fixture
def test_serve_styles_route(project_web_app):
    """Test the route for serving CSS files."""
    client = project_web_app.test_client()
    response = client.get("/styles/form.css")
    assert response.status_code == 200


@pytest.mark.flask
@pytest.mark.fixture
def test_serve_scripts_route(project_web_app):
    """Test the route for serving JavaScript files."""
    client = project_web_app.test_client()
    response = client.get("/scripts/form.js")
    assert response.status_code == 200
