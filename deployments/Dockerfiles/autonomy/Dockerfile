ARG AEA_VERSION=latest

FROM valory/open-aea-user:${AEA_VERSION}

RUN apt update

RUN apt install git net-tools sudo -y

COPY scripts /root/scripts

ENTRYPOINT ["/bin/bash", "-c"]
