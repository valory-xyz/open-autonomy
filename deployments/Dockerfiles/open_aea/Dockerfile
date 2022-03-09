ARG AEA_VERSION="latest"
FROM valory/open-aea-user:${AEA_VERSION}

WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin

RUN sudo apt-get update --fix-missing
RUN sudo apt-get autoremove
RUN sudo apt-get autoclean
RUN sudo apt-get install python3.8 python3.8-dev git -y
RUN cd /usr/bin && sudo rm python3 && sudo ln -s python3.8 python3 && sudo ln -s python3.8 python
# used in Docker-compose to wait until Hardhat node is up
RUN sudo apt-get install net-tools subversion cowsay -y

RUN python -m pip install --upgrade pip cowsay
RUN python -m pip install "open-aea[all]>=1.5.0,<2.0.0"
RUN python -m pip install "open-aea-ledger-ethereum>=1.5.0,<2.0.0"

RUN sudo apt-get install -y wget
RUN wget -O ./go-ipfs.tar.gz https://dist.ipfs.io/go-ipfs/v0.6.0/go-ipfs_v0.6.0_linux-amd64.tar.gz
RUN tar xvfz go-ipfs.tar.gz
RUN sudo mv go-ipfs/ipfs /usr/local/bin/ipfs
RUN ipfs init

WORKDIR /home/ubuntu

RUN svn checkout https://github.com/valory-xyz/open-aea/trunk/packages packages

COPY . /home/ubuntu

CMD ["start.sh"]

HEALTHCHECK --interval=3s --timeout=600s --retries=600 CMD netstat -ltn | grep -c 26658 > /dev/null; if [ 0 != $? ]; then exit 1; fi;
