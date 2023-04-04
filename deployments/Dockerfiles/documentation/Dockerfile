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

RUN pip3 install bs4==0.0.1 markdown==3.3.7 click==8.0.2 mkdocs==1.4.2 markdown-include==0.8.0 mkdocs-material==9.0.4 mkdocs-macros-plugin==0.7.0 pymdown-extensions==9.9.1 Pygments==2.14.0
RUN mkdocs build

FROM python:3.10-alpine
COPY --from=base /build/site /site

WORKDIR /site
CMD ["python3", "-m", "http.server"]
