ARG AEA_VERSION=latest
FROM valory/open-aea-user:${AEA_VERSION}

MAINTAINER Valory AG

COPY openssl.cnf /etc/ssl
COPY Pipfile /home/ubuntu/Pipfile

WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin

RUN sudo apt-get update && sudo apt-get upgrade -y
RUN sudo apt-get install python3.10 python3.10-dev git -y
RUN cd /usr/bin && sudo rm python3 && sudo ln -s python3.10 python3 && sudo ln -s python3.10 python
RUN sudo apt-get install wait-for-it net-tools -y
RUN sudo apt remove --purge python3-virtualenv

RUN python -m pip install --upgrade pip
RUN python -m pip install --force-reinstall pipenv virtualenv --user
RUN python -m pip uninstall -y setuptools
WORKDIR /home/ubuntu


COPY start_dev.sh /home/ubuntu/start_dev.sh
COPY start.sh /home/ubuntu/start.sh
COPY watcher.py /home/ubuntu/watcher.py

CMD ["./start_dev.sh"]

HEALTHCHECK --interval=3s --timeout=600s --retries=600 CMD netstat -ltn | grep -c 26658 > /dev/null; if [ 0 != $? ]; then exit 1; fi;

