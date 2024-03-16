"""Configuration file for pytest."""

import base64
import json
import os
import shutil
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Generator
from typing import Tuple

import pytest
from flask import Flask
from PIL import Image
from selenium.webdriver.common.keys import Keys
from werkzeug.datastructures import FileStorage

from tests.server import TEST_SERVER_INFO
from tests.server import build_flask_app
from tests.server import run_threaded_flask_app


def pytest_configure(config):
    """For configuring pytest with custom markers."""
    config.addinivalue_line("markers", "debug: custom marker for debugging tests.")
    config.addinivalue_line("markers", "feature: custom marker for form feature tests.")
    config.addinivalue_line("markers", "fixture: custom marker for fixture tests.")
    config.addinivalue_line("markers", "flask: custom marker for flask server tests.")
    config.addinivalue_line("markers", "schema: custom marker for schema tests.")
    config.addinivalue_line("markers", "website: custom marker for website tests.")


def get_server_info() -> Tuple[int, str]:
    """Convenience function to get test server port and submit route."""
    return TEST_SERVER_INFO["port"], TEST_SERVER_INFO["submit_route"]


def base_custom_config() -> Dict[str, Any]:
    """Defines the basic JSON config file attributes."""
    # get port and submit route
    port, submit = get_server_info()

    # build base config
    return {
        "subject": "Testing",
        "title": "Testing",
        "form_backend_url": f"http://localhost:{port}{submit}",
        "email": "foo@bar.com",
        "questions": [],
    }


def create_temp_websrc_dir(src: Path, dst: Path, src_files: Tuple[str, ...]) -> Path:
    """Create and populate a temporary directory with static web source files."""
    # create new destination subdir
    sub_dir = dst / "web_src"
    sub_dir.mkdir()

    # copy each file or directory from the project directory to the temporary directory
    for item_name in src_files:
        # get the path to the source file or directory in the project directory
        source_item_path = src / item_name

        # check if directory
        if source_item_path.is_dir():
            # if the item is a directory, recursively copy it
            shutil.copytree(source_item_path, sub_dir / item_name)

        else:
            # if the item is a file, copy it
            shutil.copy(source_item_path, sub_dir)

    return sub_dir


def load_config_file(directory: Path) -> Dict[str, Any]:
    """Load the JSON config file at directory."""
    # open the config file in the project dir
    with open(directory / "config.json", "r", encoding="utf-8") as config:
        # load the JSON data into dict
        return json.load(config)


def write_config_file(config: Dict[str, Any], src_path: Path) -> None:
    """Write out config.json file to source path."""
    # writing dictionary to JSON file with pretty printing (2 spaces indentation)
    with open(src_path / "config.json", "w") as json_file:
        json.dump(config, json_file, indent=2)


def prepare_default_config(config: Dict[str, Any], src_path: Path) -> None:
    """Update the default config copy with values approprate for testing."""
    # get port and submit route
    port, submit = get_server_info()

    # update form backend
    config["form_backend_url"] = f"http://localhost:{port}{submit}"

    # update ignore file uploads
    config["ignore_file_upload"] = False

    # update input[type=file] accept attr
    for question in config["questions"]:
        # check type
        if question["type"] == "file":
            # check for custom attr
            if "custom" in question:
                # only update accept attr
                question["custom"]["accept"] = "*"

            else:
                # add custom section with accept attr
                question["custom"] = {"accept": "*"}

    # write out updated file
    write_config_file(config, src_path)


@pytest.fixture(scope="session")
def session_tmp_dir(tmp_path_factory) -> Path:
    """Uses temporary path factory to create a session-scoped temp path."""
    # create a temporary directory using tmp_path_factory
    return tmp_path_factory.mktemp("session_temp_dir")


@pytest.fixture(scope="function")
def dummy_txt_file_path(tmp_path) -> Path:
    """Create a dummy temporary text file."""
    # create a temporary directory
    tmpdir = tmp_path / "uploads"
    tmpdir.mkdir()

    # define the file path
    file_path = tmpdir / "test_file.txt"

    # write content to the file
    with open(file_path, "w") as f:
        f.write("This is a test file.")

    return file_path


@pytest.fixture(scope="function")
def dummy_txt_file_stream(dummy_txt_file_path) -> FileStorage:
    """Create a Flask FileStorage object from text file."""
    # create a FileStorage object
    return FileStorage(stream=open(dummy_txt_file_path, "rb"), filename="test_file.txt")


@pytest.fixture(scope="function")
def dummy_txt_file_data_url(dummy_txt_file_path) -> str:
    """Create a data URL for the dummy text file."""
    # read the content of the file
    with open(dummy_txt_file_path, "rb") as f:
        file_content = f.read()

    # encode the file content as base64
    base64_content = base64.b64encode(file_content).decode("utf-8")

    # construct the data URL with the appropriate MIME type
    return f"data:text/plain;base64,{base64_content}"


@pytest.fixture(scope="function")
def dummy_form_post_data(dummy_txt_file_stream) -> Dict[str, Any]:
    """Collection of name/value pairs to simulate form post data."""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "message": "This is a test message.",
        "text_file": dummy_txt_file_stream,
    }


@pytest.fixture(scope="session")
def dummy_jpg_file_path(session_tmp_dir: Path) -> Path:
    """Create a dummy JPEG image."""
    # create image dir
    img_dir = session_tmp_dir / "images"
    img_dir.mkdir()

    # create a dummy image
    img_path = img_dir / "dummy_image.jpg"
    image = Image.new("RGB", (100, 100), color="red")  # create a red image
    image.save(img_path)

    return img_path


@pytest.fixture(scope="session")
def dummy_jpg_data_url(dummy_jpg_file_path) -> str:
    """Create a data URL for the dummy JPEG file."""
    # read the content of the file
    with open(dummy_jpg_file_path, "rb") as f:
        file_content = f.read()

    # encode the file content as base64
    base64_content = base64.b64encode(file_content).decode("utf-8")

    # construct the data URL with the appropriate MIME type
    return f"data:image/jpeg;base64,{base64_content}"


@pytest.fixture(scope="session")
def form_inputs(dummy_jpg_file_path: Path, dummy_jpg_data_url: str) -> Dict[str, Any]:
    """Defines the values to be submitted for each input type during form tests."""
    return {
        "date": {"date": "01012000"},
        "datetime-local": {
            "date": "01012000",
            "tab": Keys.TAB,
            "time": "1200",
            "period": "AM",
        },
        "email": "foo@bar.com",
        "file": (str(dummy_jpg_file_path), dummy_jpg_data_url),
        "number": "42",
        "selectbox": None,
        "tel": "18005554444",
        "text": "Sample text for input of type=text.",
        "textarea": "Sample text for Textarea.",
        "time": {"time": "1200", "period": "AM"},
        "url": "http://example.com",
    }


@pytest.fixture(scope="session")
def sb_test_url() -> str:
    """Simply defines the test URL for seleniumbase fixture testing."""
    return "https://seleniumbase.io/realworld/login"


@pytest.fixture(scope="session")
def project_directory() -> Path:
    """Get the path of the project directory."""
    # Get the path of the current file (test_file.py)
    current_file_path = Path(os.path.abspath(__file__))

    # get grand parent dir
    return current_file_path.parents[1]


@pytest.fixture(scope="session")
def website_files() -> Tuple[str, ...]:
    """Declare the files necessary for serving the website."""
    # define the files and directories to copy from the project directory
    return ("index.html", "config.json", "styles", "scripts")


@pytest.fixture(scope="session")
def session_websrc_tmp_dir(
    project_directory: Path, session_tmp_dir: Path, website_files: Tuple[str, ...]
) -> Generator[Path, None, None]:
    """Create a per-session copy of the website source code for editing."""
    # create a temporary directory
    temp_dir = create_temp_websrc_dir(project_directory, session_tmp_dir, website_files)

    # provide the temporary directory path to the test function
    yield temp_dir

    # remove the temporary directory and its contents
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def default_site_config(project_directory: Path) -> Dict[str, Any]:
    """Load the default config.json file."""
    return load_config_file(project_directory)


@pytest.fixture(scope="session")
def session_web_app(
    default_site_config: Dict[str, Any], session_websrc_tmp_dir: Path
) -> Flask:
    """Create a session-scoped Flask app for testing with the website source."""
    # now update config.json with new backend url
    prepare_default_config(default_site_config, session_websrc_tmp_dir)

    # create app
    return build_flask_app(session_websrc_tmp_dir)


@pytest.fixture(scope="session")
def live_session_web_app_url(session_web_app: Flask) -> str:
    """Runs session-scoped Flask app in a thread."""
    # get port
    port = session_web_app.config.get("PORT")
    assert port is not None

    # start threaded app
    run_threaded_flask_app(session_web_app)

    # get url
    return f"http://localhost:{port}"


@pytest.fixture(scope="function")
def multiple_select_options_config() -> Dict[str, Any]:
    """Custom config file fixture for testing multiple select options."""
    # get base config
    config = base_custom_config()

    # update questions
    config["questions"] = [
        {
            "label": "Select your country",
            "name": "country",
            "type": "selectbox",
            "required": True,
            "options": [
                {
                    "label": "--Select all that apply--",
                    "value": "",
                    "selected": True,
                    "disabled": True,
                },
                {"label": "USA", "value": "USA"},
                {"label": "Canada", "value": "CAN"},
                {"label": "United Kingdom", "value": "UK"},
                {"label": "Australia", "value": "AUS"},
            ],
            "custom": {"multiple": True},
        }
    ]

    # updated
    return config


@pytest.fixture(scope="function")
def ignore_upload_config() -> Dict[str, Any]:
    """Custom config file fixture for testing ignore file uploads."""
    # get base config
    config = base_custom_config()

    # set ignore
    config["ignore_file_upload"] = True

    # update questions
    config["questions"] = [
        {
            "label": "Upload funny memes",
            "name": "meme_imgs",
            "type": "file",
            "required": True,
            "custom": {
                "multiple": True,
                "accept": "*",
            },
        }
    ]

    # updated
    return config


@pytest.fixture(scope="function")
def instructions_config() -> Dict[str, Any]:
    """Custom config file fixture with multiline instructions."""
    # get base config
    config = base_custom_config()

    # set ignore
    config["instructions"] = [
        "<p>",
        "Fill out the form below, and click <b>Send</b> to submit it.",
        "If that should fail, simply click <b>Download Form</b> and manually",
        "email the completed form to:",
        "<strong class='email-placeholder'>[Email Address]</strong>.",
        "</p>",
    ]

    # update questions
    config["questions"] = [
        {
            "label": "Question 1",
            "name": "q1",
            "type": "text",
            "required": True,
        }
    ]

    # updated
    return config
