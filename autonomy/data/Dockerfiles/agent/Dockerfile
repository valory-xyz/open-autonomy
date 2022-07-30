ARG AEA_VERSION=latest
FROM valory/open-aea-user:${AEA_VERSION}
ARG AUTHOR=default_author
ARG AEA_AGENT

COPY openssl.cnf /etc/ssl
COPY Pipfile .
COPY . /home/ubuntu

WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin

RUN sudo apt-get update --fix-missing
RUN sudo apt-get autoremove
RUN sudo apt-get autoclean
RUN sudo apt-get install python3.10 python3.10-dev git -y
RUN cd /usr/bin && sudo rm python3 && sudo ln -s python3.10 python3 && sudo ln -s python3.10 python
# used in Docker-compose to wait until Hardhat node is up
RUN sudo apt-get install net-tools -y
RUN python -m pip install --upgrade pip

WORKDIR /home/ubuntu

RUN python -m pip install --force-reinstall pipenv virtualenv --user
RUN sudo pipenv --python 3.10
RUN pipenv install --system --skip-lock
RUN aea init --reset --remote --ipfs --author ${AUTHOR}

VOLUME /home/ubuntu/logs

RUN INSTALL=1 VALORY_APPLICATION=${AEA_AGENT} bash start.sh
CMD ["start.sh"]

HEALTHCHECK --interval=3s --timeout=600s --retries=600 CMD netstat -ltn | grep -c 26658 > /dev/null; if [ 0 != $? ]; then exit 1; fi;
