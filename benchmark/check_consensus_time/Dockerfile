FROM valory/open-aea-user

WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin

RUN sudo apt-get install python3.8 python3.8-dev -y
RUN cd /usr/bin && sudo rm python3 && sudo ln -s python3.8 python3 && sudo ln -s python3.8 python
# used in Docker-compose to wait until Hardhat node is up
RUN sudo apt-get install wait-for-it -y

RUN python3.8 -m pip install --upgrade pip
RUN python3.8 -m pip install "open-aea[all]>=1.3.0,<2.0.0"

COPY packages /home/ubuntu/packages

RUN aea fetch --local valory/price_estimation:0.1.0

WORKDIR /home/ubuntu/price_estimation
RUN aea install

COPY benchmark/check_consensus_time/run.sh /home/ubuntu/run.sh
COPY benchmark/check_consensus_time/configure_agents /home/ubuntu/configure_agents
RUN sudo chown -R ubuntu:ubuntu /home/ubuntu/configure_agents
RUN sudo chmod +x /home/ubuntu/configure_agents/*.sh

CMD ["aea", "run"]
