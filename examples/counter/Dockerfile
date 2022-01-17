FROM valory/open-aea-user

WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin
RUN alias python='python3'

RUN pip install "open-aea[all]>=1.3.0,<2.0.0"
RUN pip install "open-aea-ledger-ethereum>=1.3.2,<2.0.0"

COPY packages /home/ubuntu/packages

RUN aea fetch --local valory/counter:0.1.0
RUN cd counter && aea generate-key ethereum

WORKDIR /home/ubuntu/counter
CMD ["aea", "run"]
