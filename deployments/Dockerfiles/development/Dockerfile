ARG AEA_VERSION=latest

FROM valory/open-aea-user:${AEA_VERSION}

ARG AUTHOR=default_author

RUN apt remove --purge python3-virtualenv
RUN python -m pip uninstall -y setuptools
RUN python -m pip install --upgrade pip
RUN python -m pip install --force-reinstall pipenv virtualenv requests

WORKDIR /root

COPY Pipfile /root/Pipfile
COPY watcher.py /root/watcher.py
COPY run.sh /root/run.sh
COPY entrypoint.sh /root/entrypoint.sh

CMD ["/root/entrypoint.sh"]

HEALTHCHECK --interval=3s --timeout=600s --retries=600 CMD netstat -ltn | grep -c 26658 > /dev/null; if [ 0 != $? ]; then exit 1; fi;
