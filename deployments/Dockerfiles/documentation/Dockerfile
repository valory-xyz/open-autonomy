FROM ubuntu:22.04 as base
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y                                                       \
       python3-venv                                                          \
       python3-pip                                                           \
       python3-dev                                                           \
       git

# needed by Pipenv
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN mkdir /build
WORKDIR /build

COPY docs/ /build/docs
COPY mkdocs.yml /build

RUN pip3 install tomte[docs]==0.2.17
RUN mkdocs build

FROM python:3.10-alpine
COPY --from=base /build/site /site

WORKDIR /site
CMD ["python3", "-m", "http.server"]
