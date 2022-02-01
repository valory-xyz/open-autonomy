FROM valory/open-aea-user


WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin

RUN sudo apt-get install python3.8 python3.8-dev git -y
RUN cd /usr/bin && sudo rm python3 && sudo ln -s python3.8 python3 && sudo ln -s python3.8 python
# used in Docker-compose to wait until Hardhat node is up
RUN sudo apt-get install wait-for-it -y

RUN python -m pip install --upgrade pip
RUN python -m pip install "open-aea[all]>=1.3.0,<2.0.0"

WORKDIR /home/ubuntu

COPY packages /home/ubuntu/packages

RUN aea fetch --local valory/price_estimation:0.1.0

WORKDIR /home/ubuntu/price_estimation
RUN aea install

COPY examples/price_estimation/run.sh /home/ubuntu/run.sh
COPY examples/price_estimation/configure_agents /home/ubuntu/configure_agents
RUN sudo chown -R ubuntu:ubuntu /home/ubuntu/configure_agents

CMD ["aea", "run"]
