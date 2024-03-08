[![tests](https://github.com/DiogenesAnalytics/parley/actions/workflows/tests.yml/badge.svg)](https://github.com/DiogenesAnalytics/parley/actions/workflows/tests.yml)
[![docker](https://github.com/DiogenesAnalytics/parley/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/DiogenesAnalytics/parley/actions/workflows/docker-publish.yml)
[![pages-build-deployment](https://github.com/DiogenesAnalytics/parley/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/DiogenesAnalytics/parley/actions/workflows/pages/pages-build-deployment)

# Parley
*(noun)*

**Pronunciation:** /ˈpɑːrli/

**Definition:**
A formal discussion or negotiation between parties, especially enemies, typically to resolve a conflict or dispute peacefully. It often implies a temporary truce or cessation of hostilities to facilitate dialogue.

**Example Sentence:**
The warring factions agreed to a parley at the neutral ground to seek a diplomatic solution to their long-standing conflict.

## Development
Here we introduce the various tools related to *developing* the `Parley`
software.

### Make
A `Makefile` is available in the project root, and implements several commands to
make the *development process* easier. All *commands*  are executed by the following
format: `make [COMMAND]`. To see the *contents* of a command that will be executed upon
invocation of the command, simply run `make -n [COMMAND]` (**NOTE**: this serves as a
good way to test a command and see what **exactly** will be executed before running the
command). Below is the list of the commands and their short descriptions:

+ `build`: Build the Docker image
+ `serve`: Serve the website
+ `server-container`: Build server container
+ `pause`: Pause 1 second (to pause between commands)
+ `address`: Get Docker container address/port
+ `stop-server`: Stop the running web server
+ `restart-server`: Restart the running web server
+ `lint`: Run linters
+ `test`: Run full testing suite
+ `pytest`: Run pytest in Docker container
+ `isort`: Run isort in Docker container
+ `black`: Run black in Docker container
+ `flake8`: Run flake8 in Docker container
+ `mypy`: Run mypy in Docker container
+ `shell`: Create interactive shell in Docker container

#### Example Uses
Here we will show some **common use cases** for the `Makefile`:

+ **serve the website locally**: running the `make serve` will serve the website and
  print out the *host*/*address* to your terminal.

+ **test the website locally**: running the `make pytest` will run **ONLY** the *Python*
  tests (written with *pytest*) on the current website.

+ **build docker image**: running `make build` will build the
  `ghcr.io/diogenesanalytics/parley:master` *Docker image* locally.

+ **stop the web server**: running `make stop-server` will stop any currently *running*
  server deployed by `make serve`.

+ **get local server address**: running `make address` will get the *host*/*port* for
  the server deployed previously by `make serve` (if any exist).

+ **run specific tests**: running `make shell` will allow start up a **bash** instance
  inside the `ghcr.io/diogenesanalytics/parley:master` *Docker image*, from which you
  can then run a *specific subset* of tests (**e.g.** `pytest -m website`).
