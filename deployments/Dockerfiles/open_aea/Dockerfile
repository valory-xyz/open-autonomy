FROM valory/open-aea-user:latest

WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin

RUN sudo apt-get update --fix-missing
RUN sudo apt-get autoremove
RUN sudo apt-get autoclean
RUN sudo apt-get install python3.8 python3.8-dev git -y
RUN cd /usr/bin && sudo rm python3 && sudo ln -s python3.8 python3 && sudo ln -s python3.8 python
# used in Docker-compose to wait until Hardhat node is up
RUN sudo apt-get install wait-for-it subversion cowsay -y

RUN python -m pip install --upgrade pip cowsay
RUN python -m pip install "open-aea[all]>=1.5.0,<2.0.0"
RUN python -m pip install "open-aea-ledger-ethereum>=1.5.0,<2.0.0"

WORKDIR /home/ubuntu

copy . /home/ubuntu

RUN sudo apt-get install -y wget
RUN wget -O ./go-ipfs.tar.gz https://dist.ipfs.io/go-ipfs/v0.6.0/go-ipfs_v0.6.0_linux-amd64.tar.gz
RUN tar xvfz go-ipfs.tar.gz
RUN sudo mv go-ipfs/ipfs /usr/local/bin/ipfs
RUN ipfs init


CMD ["start.sh"]
