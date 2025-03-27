# Base image
FROM python:3.10-slim-bullseye AS base
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update -y && apt-get install gcc git make libssl-dev libffi-dev -y && rm -rf /var/lib/apt/lists/*

# Install library dependencies into our venv
RUN python3 -m venv $VIRTUAL_ENV
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Customize base image with agent deps
FROM python:3.10-slim-bullseye AS agent_deps
ARG AUTHOR=user

# Install docker
VOLUME /var/run/docker.sock
RUN apt-get update -y && apt-get install curl -y
RUN curl -sSL https://get.docker.com/ | sh

ENV VIRTUAL_ENV=/opt/venv
COPY --from=base $VIRTUAL_ENV $VIRTUAL_ENV

RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Setup autonomy and prepare image
RUN autonomy init --remote --ipfs --reset --author $AUTHOR

ENTRYPOINT [ "/bin/bash"]
