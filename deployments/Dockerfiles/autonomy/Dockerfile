ARG AEA_VERSION=latest

FROM valory/open-aea-user:${AEA_VERSION}

VOLUME /var/run/docker.sock
RUN apt update

RUN apt install git net-tools sudo curl -y

RUN curl -sSL https://get.docker.com/ | sh

COPY scripts /root/scripts

RUN chmod -R a+x /root

ENTRYPOINT ["/bin/bash", "-c"]
