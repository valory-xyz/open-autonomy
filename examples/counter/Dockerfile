FROM fetchai/aea-user:1.0.2

WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin
RUN alias python='python3'

RUN pip install "aea[all]>=1.0.0,<2.0.0"
RUN pip install "aea-ledger-ethereum>=1.0.0,<2.0.0"

COPY packages /home/ubuntu/packages

RUN aea fetch valory/counter:0.1.0
RUN cd counter && aea generate-key ethereum

WORKDIR /home/ubuntu/counter
CMD ["aea", "run"]
