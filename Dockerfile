# get python base image
FROM python:3.11

# set workdir
WORKDIR /usr/local/src/parley

# copy source
COPY . .

# install requirements
RUN pip3 install -r tests/requirements.txt
