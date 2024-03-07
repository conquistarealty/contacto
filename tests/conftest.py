"""Configuration file for pytest."""

import json
import os
import shutil
import threading
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Generator
from typing import Tuple

import pytest
from flask import Flask
from flask import render_template
from flask import request
from flask import send_from_directory
from selenium.webdriver.common.keys import Keys


def pytest_configure(config):
    """For configuring pytest with custom markers."""
    config.addinivalue_line("markers", "schema: custom marker for schema tests.")
    config.addinivalue_line("markers", "fixture: custom marker for fixture tests.")
    config.addinivalue_line("markers", "website: custom marker for website tests.")
    config.addinivalue_line("markers", "flask: custom marker for flask server tests.")


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


def build_flask_app(serve_directory: Path, port: int, submit_route: str) -> Flask:
    """Assembles Flask app to serve static site."""
    # instantiate app
    app = Flask(__name__)

    # update the port
    app.config["PORT"] = port

    # define routes
    @app.route("/")
    def index():
        """Serve the index file in the project dir."""
        return send_from_directory(serve_directory, "index.html")

    @app.route("/<path:path>")
    def other_root_files(path):
        """Serve any other files (e.g. config.json) from the project dir."""
        return send_from_directory(serve_directory, path)

    @app.route("/styles/<path:path>")
    def serve_styles(path):
        """Send any CSS files from the temp dir."""
        css_file = os.path.join("styles", path)
        if os.path.exists(os.path.join(serve_directory, css_file)):
            return send_from_directory(serve_directory, css_file)
        else:
            return "CSS file not found\n", 404

    @app.route("/scripts/<path:path>")
    def serve_scripts(path):
        """Send any JavaScript files from the temp dir."""
        js_file = os.path.join("scripts", path)
        if os.path.exists(os.path.join(serve_directory, js_file)):
            return send_from_directory(serve_directory, js_file)
        else:
            return "JavaScript file not found\n", 404

    @app.route(submit_route, methods=["POST"])
    def submit_form():
        # access form data submitted by the client
        form_data = request.form

        # log data
        print(request.form)

        # render the template with the form data
        return render_template("form_response_template.html", form_data=form_data)

    # return configured and route decorated Flask app
    return app


def run_threaded_flask_app(app: Flask) -> None:
    """Run a Flask app using threading."""
    # launch Flask app for projecf dir in thread
    thread = threading.Thread(target=app.run)
    thread.daemon = True
    thread.start()


def load_config_file(directory: Path) -> Dict[str, Any]:
    """Load the JSON config file at directory."""
    # open the config file in the project dir
    with open(directory / "config.json", "r", encoding="utf-8") as config:
        # load the JSON data into dict
        return json.load(config)


def update_form_backend_config(
    config: Dict[str, Any], src_path: Path, port: int
) -> None:
    """Set the form backend url to testing server url."""
    # update form backend
    config["form_backend_url"] = f"http://localhost:{port}/submit"

    # Writing dictionary to JSON file with pretty printing (2 spaces indentation)
    with open(src_path / "config.json", "w") as json_file:
        json.dump(config, json_file, indent=2)


@pytest.fixture(scope="session")
def form_inputs() -> Dict[str, Any]:
    """Defines the values to be submitted for each input type during form tests."""
    return {
        "email": "foo@bar.com",
        "date": {"date": "01012000"},
        "datetime-local": {
            "date": "01012000",
            "tab": Keys.TAB,
            "time": "1200",
            "period": "AM",
        },
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
def session_tmp_dir(tmp_path_factory) -> Path:
    """Uses temporary path factory to create a session-scoped temp path."""
    # create a temporary directory using tmp_path_factory
    return tmp_path_factory.mktemp("session_temp_dir")


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


@pytest.fixture(scope="function")
def function_websrc_tmp_dir(
    project_directory: Path, tmp_path: Path, website_files: Tuple[str, ...]
) -> Generator[Path, None, None]:
    """Create a per-function copy of the website source code for editing."""
    # create a temporary directory
    temp_dir = create_temp_websrc_dir(project_directory, tmp_path, website_files)

    # provide the temporary directory path to the test function
    yield temp_dir

    # remove the temporary directory and its contents
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def default_site_config(project_directory: Path) -> Dict[str, Any]:
    """Load the default config.json file."""
    return load_config_file(project_directory)


@pytest.fixture(scope="session")
def submit_route() -> str:
    """Defines the route used for the form submission testing."""
    return "/submit"


@pytest.fixture(scope="session")
def session_web_app(
    default_site_config: Dict[str, Any], session_websrc_tmp_dir: Path, submit_route: str
) -> Flask:
    """Create a session-scoped Flask app for testing with the website source."""
    # set port
    port = 5000

    # now update config.json with new backend url
    update_form_backend_config(default_site_config, session_websrc_tmp_dir, port)

    # create app
    return build_flask_app(session_websrc_tmp_dir, port, submit_route)


@pytest.fixture(scope="session")
def live_session_web_app_url(session_web_app: Flask) -> str:
    """Runs session-scoped Flask app in a thread."""
    # start threaded app
    run_threaded_flask_app(session_web_app)

    # get port
    port = session_web_app.config.get("PORT")

    # get url
    return f"http://localhost:{port}"
