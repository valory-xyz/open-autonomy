FROM fetchai/aea-user:1.0.2

ARG agent_id

WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin
RUN alias python='python3'

RUN pip install "aea[all]>=1.0.0,<2.0.0"
RUN pip install "aea-ledger-ethereum>=1.0.0,<2.0.0"

COPY packages /home/ubuntu/packages
COPY examples/price_estimation/configure_agents configure_agents

RUN aea fetch valory/price_estimation:0.1.0
RUN cd price_estimation && aea generate-key ethereum
RUN ../configure_agents/${ARG}.sh

WORKDIR /home/ubuntu/price_estimation
CMD ["aea", "run"]
