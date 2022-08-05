FROM valory/open-aea-user:latest
ARG AEA_AGENT

RUN sudo apt-get update --fix-missing
RUN sudo apt-get autoremove
RUN sudo apt-get autoclean

RUN sudo apt-get install python3.10 python3.10-dev git -y
RUN cd /usr/bin && sudo rm python3 && sudo ln -s python3.10 python3 && sudo ln -s python3.10 python
RUN sudo apt-get install net-tools -y

WORKDIR /home/ubuntu

COPY openssl.cnf /etc/ssl
COPY requirements.txt .
COPY start.sh .

ENV PATH=$PATH:/home/ubuntu/.local/bin

RUN python -m pip install --upgrade pip
RUN python -m pip install --force-reinstall pipenv virtualenv --user
RUN python -m pip install -r requirements.txt 

RUN aea init --reset --remote --ipfs --author default_author
CMD ["start.sh"]
HEALTHCHECK --interval=3s --timeout=600s --retries=600 CMD netstat -ltn | grep -c 26658 > /dev/null; if [ 0 != $? ]; then exit 1; fi;
