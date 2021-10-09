FROM fetchai/aea-user:1.0.2


WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin

RUN sudo apt-get install python3.7 python3.7-dev -y
RUN cd /usr/bin && sudo rm python3 && sudo ln -s python3.7 python3 && sudo ln -s python3.7 python
# used in Docker-compose to wait until Hardhat node is up
RUN sudo apt-get install wait-for-it -y

RUN python -m pip install --upgrade pip
RUN python -m pip install "aea[all]>=1.0.0,<2.0.0"

# --no-deps needed because we need web3 higher than 5.12
RUN python -m pip install "aea-ledger-ethereum>=1.0.0,<2.0.0" --no-deps
RUN python -m pip install "ipfshttpclient==0.8.0a2"
RUN python -m pip install "web3>=5.23.0,<=5.24.0"
RUN python -m pip install "py-eth-sig-utils==0.4.0"

COPY packages /home/ubuntu/packages

RUN aea fetch valory/price_estimation:0.1.0

WORKDIR /home/ubuntu/price_estimation

COPY examples/price_estimation/run.sh /home/ubuntu/run.sh
COPY examples/price_estimation/configure_agents /home/ubuntu/configure_agents
RUN sudo chown -R ubuntu:ubuntu /home/ubuntu/configure_agents

CMD ["aea", "run"]
