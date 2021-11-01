FROM valory/open-aea-user


WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin

RUN sudo apt-get install python3.7 python3.7-dev git -y
RUN cd /usr/bin && sudo rm python3 && sudo ln -s python3.7 python3 && sudo ln -s python3.7 python
# used in Docker-compose to wait until Hardhat node is up
RUN sudo apt-get install wait-for-it -y

RUN python -m pip install --upgrade pip
RUN python -m pip install "open-aea[all]>=1.0.0,<2.0.0"

COPY packages /home/ubuntu/packages



RUN aea fetch --local valory/price_estimation:0.1.0

WORKDIR /home/ubuntu/price_estimation
RUN aea install

WORKDIR /home/ubuntu
RUN pip uninstall aea -y
RUN git clone https://github.com/valory-xyz/open-aea.git
WORKDIR /home/ubuntu/open-aea
RUN git submodule sync --recursive && git submodule update --init --recursive
RUN pip install .[all]
WORKDIR /home/ubuntu/price_estimation

COPY examples/price_estimation/run.sh /home/ubuntu/run.sh
COPY examples/price_estimation/configure_agents /home/ubuntu/configure_agents
RUN sudo chown -R ubuntu:ubuntu /home/ubuntu/configure_agents

CMD ["aea", "run"]
