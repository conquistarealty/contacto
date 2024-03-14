"""Configuration file for pytest."""

import base64
import json
import os
import random
import shutil
import threading
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Generator
from typing import Set
from typing import Tuple

import pytest
from flask import Flask
from flask import render_template
from flask import request
from flask import send_from_directory
from PIL import Image
from selenium.webdriver.common.keys import Keys
from werkzeug.datastructures import FileStorage
from werkzeug.datastructures import ImmutableMultiDict


def pytest_configure(config):
    """For configuring pytest with custom markers."""
    config.addinivalue_line("markers", "debug: custom marker for debugging tests.")
    config.addinivalue_line("markers", "feature: custom marker for form feature tests.")
    config.addinivalue_line("markers", "fixture: custom marker for fixture tests.")
    config.addinivalue_line("markers", "flask: custom marker for flask server tests.")
    config.addinivalue_line("markers", "schema: custom marker for schema tests.")
    config.addinivalue_line("markers", "website: custom marker for website tests.")


def generate_unique_random_ports(num_ports: int) -> Generator[int, None, None]:
    """Generator that only yield unique random ports."""
    # create set of used ports
    used_ports: Set[int] = set()

    # loop over ports
    while len(used_ports) < num_ports:
        # get random port
        port = random.randint(5001, 65535)

        # check it is unique
        if port not in used_ports:
            # send it forward
            yield port

            # mark it as used
            used_ports.add(port)


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


def get_html_tag_from_mimetype(file: FileStorage, encoded_data: str) -> str:
    """Generate an HTML tag based on the MIME type of the file."""
    # create data URL for reuse below
    data_url = f"data:{file.mimetype};base64,{encoded_data}"

    # match the mimetype
    match file.mimetype.split("/")[0]:
        case "image":
            tag = f"<img src={data_url!r}>"
        case "video":
            tag = (
                f"<video controls>"
                f"    <source src={data_url!r} type={file.mimetype!r}>"
                f"    Your browser does not support the video tag."
                f"</video>"
            )
        case "audio":
            tag = (
                f"<audio controls>"
                f"    <source src={data_url!r} type={file.mimetype!r}>"
                f"    Your browser does not support the audio tag."
                f"</audio>"
            )
        case _:
            tag = f"<a href={data_url!r}>Download {file.filename}</a>"

    return tag


def process_form_data(form_data: ImmutableMultiDict) -> Dict[str, Any]:
    """Process form data to handle multi-values."""
    # setup processed results
    processed_data: Dict[str, Any] = {}

    # check form key/values
    for key, value in form_data.items(multi=True):
        # check if key indicates file(s)
        if key in request.files:
            processed_data[key] = ""

        # check to see if there are multiple values
        elif key in processed_data:
            processed_data[key] += f", {value}"

        # handle normally
        else:
            processed_data[key] = value

    return processed_data


def process_uploaded_files(processed_data: Dict[str, Any]) -> None:
    """Process uploaded files and generate HTML tags."""
    # get list of tuples for key/files pairs
    for key, files in request.files.lists():
        # loop over each file
        for file in files:
            # make sure it exists
            if file.filename:
                # get data from file
                file_data = file.read()

                # convert to base64 for data URL creation later ...
                encoded_data = base64.b64encode(file_data).decode("utf-8")

                # create tag
                tag = get_html_tag_from_mimetype(file, encoded_data)

                # update current results
                if key in processed_data:
                    processed_data[key] += "<br>" + tag
                else:
                    processed_data[key] = tag


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
        """Render HTML form data as a response form."""
        # log data
        print(f"Form data received: {request.form}")

        # process data
        processed_data = process_form_data(request.form)

        # log processed data
        print(f"Processed data: {processed_data}")

        # process any files
        process_uploaded_files(processed_data)

        # log files added
        print(f"Added uploaded files: {processed_data}")

        # now render response
        return render_template("form_response_template.html", form_data=processed_data)

    # return configured and route decorated Flask app
    return app


def run_threaded_flask_app(app: Flask, port: int) -> None:
    """Run a Flask app using threading."""
    # launch Flask app for project dir in thread
    thread = threading.Thread(target=app.run, kwargs={"port": port})
    thread.daemon = True
    thread.start()


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


def prepare_default_config(config: Dict[str, Any], src_path: Path, port: int) -> None:
    """Update the default config copy with values approprate for testing."""
    # update form backend
    config["form_backend_url"] = f"http://localhost:{port}/submit"

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
    prepare_default_config(default_site_config, session_websrc_tmp_dir, port)

    # create app
    return build_flask_app(session_websrc_tmp_dir, port, submit_route)


@pytest.fixture(scope="session")
def live_session_web_app_url(session_web_app: Flask) -> str:
    """Runs session-scoped Flask app in a thread."""
    # get port
    port = session_web_app.config.get("PORT")
    assert port is not None

    # start threaded app
    run_threaded_flask_app(session_web_app, port)

    # get url
    return f"http://localhost:{port}"


@pytest.fixture(scope="function")
def unique_random_port() -> int:
    """Generate a unique random port greater than 5000."""
    # control the number of ports generated
    num_ports = 100
    return next(generate_unique_random_ports(num_ports))


@pytest.fixture(scope="function")
def function_web_app(
    function_websrc_tmp_dir: Path, submit_route: str, unique_random_port: int
) -> Flask:
    """Create a function-scoped Flask app for testing with the website source."""
    # create app
    return build_flask_app(function_websrc_tmp_dir, unique_random_port, submit_route)


@pytest.fixture(scope="function")
def live_function_web_app_url(function_web_app: Flask) -> str:
    """Runs session-scoped Flask app in a thread."""
    # get port
    port = function_web_app.config.get("PORT")
    assert port is not None

    # start threaded app
    run_threaded_flask_app(function_web_app, port)

    # get url
    return f"http://localhost:{port}"


@pytest.fixture(scope="function")
def multiple_select_options_config() -> Dict[str, Any]:
    """Custom config file fixture for testing multiple select options."""
    return {
        "subject": "Testing Multiple Select Options",
        "title": "Testing Multi-Select Options",
        "form_backend_url": None,
        "email": "foo@bar.com",
        "questions": [
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
        ],
    }
