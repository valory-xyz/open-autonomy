FROM valory/open-aea-user:latest

WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin

RUN sudo apt-get install python3.8 python3.8-dev git -y
RUN cd /usr/bin && sudo rm python3 && sudo ln -s python3.8 python3 && sudo ln -s python3.8 python
# used in Docker-compose to wait until Hardhat node is up
RUN sudo apt-get install wait-for-it subversion cowsay -y

RUN python -m pip install --upgrade pip cowsay
RUN python -m pip install "open-aea[all]>=1.4.0.post1,<2.0.0"
RUN python -m pip install "open-aea-ledger-ethereum>=1.2.0,<2.0.0"

WORKDIR /home/ubuntu

RUN svn checkout https://github.com/valory-xyz/open-aea/trunk/packages packages

copy . /home/ubuntu

CMD ["start.sh"]
