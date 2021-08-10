FROM fetchai/aea-user:1.0.2


WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin
RUN alias python='python3'

RUN pip install "aea[all]>=1.0.0,<2.0.0"
RUN pip install "aea-ledger-ethereum>=1.0.0,<2.0.0"

COPY packages /home/ubuntu/packages

RUN aea fetch valory/price_estimation:0.1.0

WORKDIR /home/ubuntu/price_estimation
RUN aea install

COPY examples/price_estimation/run.sh /home/ubuntu/run.sh
COPY examples/price_estimation/configure_agents /home/ubuntu/configure_agents
RUN sudo chown -R ubuntu:ubuntu /home/ubuntu/configure_agents

CMD ["aea", "run"]
