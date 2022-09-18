# Base image
FROM python:3.10-slim-bullseye as base
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update -y && apt-get install gcc -y && rm -rf /var/lib/apt/lists/*

# Install library dependencies into our venv
RUN python3 -m venv $VIRTUAL_ENV
COPY requirements.txt .
RUN pip install -r requirements.txt

# Customize base image with agent deps
FROM python:3.10-slim-bullseye as agent_deps
ARG AUTHOR=user

ENV VIRTUAL_ENV=/opt/venv
COPY --from=base $VIRTUAL_ENV $VIRTUAL_ENV

RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Setup autonomy and prepare image
RUN autonomy init --remote --ipfs --reset --author $AUTHOR

ENTRYPOINT [ "/bin/bash"]
