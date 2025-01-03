FROM python:3.11-slim as base

RUN apt-get update && apt-get install -y git

WORKDIR /build

COPY docs/ /build/docs
COPY mkdocs.yml /build

RUN pip install --no-cache-dir \
    mkdocs-material \
    mkdocstrings[python] \
    mkdocs-include-markdown-plugin \
    mkdocs-macros-plugin

RUN pip install -e .
RUN mkdocs build

FROM python:3.11-alpine
COPY --from=base /build/site /site

WORKDIR /site
CMD ["python3", "-m", "http.server"]
