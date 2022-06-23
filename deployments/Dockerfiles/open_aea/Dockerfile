ARG AEA_VERSION=latest
FROM valory/open-aea-user:${AEA_VERSION}
ARG AEA_AGENT

COPY openssl.cnf /etc/ssl

WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin

RUN sudo apt-get update --fix-missing
RUN sudo apt-get autoremove
RUN sudo apt-get autoclean
RUN sudo apt-get install python3.10 python3.10-dev git -y
RUN cd /usr/bin && sudo rm python3 && sudo ln -s python3.10 python3 && sudo ln -s python3.10 python
# used in Docker-compose to wait until Hardhat node is up
RUN sudo apt-get install net-tools subversion -y
RUN python -m pip install --upgrade pip

RUN sudo apt-get install -y wget
RUN wget -O ./go-ipfs.tar.gz https://dist.ipfs.io/go-ipfs/v0.6.0/go-ipfs_v0.6.0_linux-amd64.tar.gz
RUN tar xvfz go-ipfs.tar.gz
RUN sudo mv go-ipfs/ipfs /usr/local/bin/ipfs
RUN ipfs init

WORKDIR /home/ubuntu

COPY Pipfile .
RUN python -m pip install --force-reinstall pipenv virtualenv --user
RUN sudo pipenv --python 3.10
RUN pipenv install --system --skip-lock

RUN svn checkout https://github.com/valory-xyz/open-aea/trunk/packages packages

COPY . /home/ubuntu
VOLUME /home/ubuntu/logs

RUN INSTALL=1 VALORY_APPLICATION=${AEA_AGENT} bash start.sh

CMD ["start.sh"]

HEALTHCHECK --interval=3s --timeout=600s --retries=600 CMD netstat -ltn | grep -c 26658 > /dev/null; if [ 0 != $? ]; then exit 1; fi;
