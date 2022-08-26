ARG AEA_VERSION=latest

FROM valory/open-aea-user:${AEA_VERSION}

COPY openssl.cnf /etc/ssl
COPY requirements.txt /home/ubuntu

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

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "/bin/bash" ]
