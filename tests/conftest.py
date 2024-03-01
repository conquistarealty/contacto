"""Configuration file for pytest."""

import os
import shutil
from pathlib import Path
from typing import Generator
from typing import Tuple

import pytest


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
