FROM valory/open-aea-user


WORKDIR /home/ubuntu
ENV PATH=$PATH:/home/ubuntu/.local/bin

RUN sudo apt-get install python3.8 python3.8-dev git -y
RUN cd /usr/bin && sudo rm python3 && sudo ln -s python3.8 python3 && sudo ln -s python3.8 python
RUN sudo apt-get install wait-for-it -y pipenv

RUN python -m pip install --upgrade pip
RUN python -m pip install click Wheel watchdog requests --user
RUN python -m pip install "open-aea[all]>=1.4.0,<2.0.0" --user
RUN python -m pip install open-aea-cli-ipfs==1.3.1 open-aea-ledger-cosmos open-aea-ledger-ethereum==1.4.1 --user

WORKDIR /home/ubuntu

COPY configure_agents /home/ubuntu/configure_agents
COPY watcher.py /home/ubuntu/watcher.py

RUN sudo chown -R ubuntu:ubuntu /home/ubuntu/configure_agents
RUN sudo chmod +x /home/ubuntu/configure_agents/*.sh

ENTRYPOINT ["/bin/bash"]
