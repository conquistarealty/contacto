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
from flask import send_from_directory


def pytest_configure(config):
    """For configuring pytest with custom markers."""
    config.addinivalue_line("markers", "schema: custom marker for schema tests.")
    config.addinivalue_line("markers", "fixture: custom marker for fixture tests.")
    config.addinivalue_line("markers", "website: custom marker for website tests.")
    config.addinivalue_line("markers", "flask: custom marker for flask server tests.")


def build_flask_app(serve_directory: Path, port: int) -> Flask:
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

    return app


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
def project_web_app(project_directory: Path):
    """Create a Flask app for testing with the website source."""
    return build_flask_app(project_directory, 5000)


@pytest.fixture(scope="session")
def live_project_web_app_url(request, project_web_app: Flask):
    """Runs Flask app for project directory in a thread."""
    # launch Flask app for projecf dir in thread
    thread = threading.Thread(target=project_web_app.run)
    thread.daemon = True
    thread.start()

    # get port
    assert "PORT" in project_web_app.config, "PORT key not set"
    port = project_web_app.config.get("PORT")

    # get url
    return f"http://localhost:{port}"


@pytest.fixture(scope="session")
def website_files() -> Tuple[str, ...]:
    """Declare the files necessary for serving the website."""
    # define the files and directories to copy from the project directory
    return ("index.html", "config.json", "styles", "scripts")


@pytest.fixture(scope="function")
def temp_web_src(
    project_directory: Path, tmp_path: Path, website_files: Tuple[str, ...]
) -> Generator[Path, None, None]:
    """Create a copy of the website source code for editing."""
    # create a temporary directory
    temp_dir = tmp_path / "web_src"
    temp_dir.mkdir()

    # copy each file or directory from the project directory to the temporary directory
    for item_name in website_files:
        # get the path to the source file or directory in the project directory
        source_item_path = project_directory / item_name

        # check if directory
        if source_item_path.is_dir():
            # if the item is a directory, recursively copy it
            shutil.copytree(source_item_path, temp_dir / item_name)

        else:
            # if the item is a file, copy it
            shutil.copy(source_item_path, temp_dir)

    # provide the temporary directory path to the test function
    yield temp_dir

    # remove the temporary directory and its contents
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def default_site_config(project_directory: Path) -> Dict[str, Any]:
    """Load the default config.json file."""
    # open the config file in the project dir
    with open(project_directory / "config.json", "r", encoding="utf-8") as config:
        # load the JSON data into dict
        return json.load(config)
