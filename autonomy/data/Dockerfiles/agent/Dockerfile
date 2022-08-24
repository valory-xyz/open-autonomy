ARG AUTONOMY_IMAGE_VERSION="latest"
ARG AUTONOMY_IMAGE_NAME="valory/open-autonomy"

FROM ${AUTONOMY_IMAGE_NAME}:${AUTONOMY_IMAGE_VERSION}

ARG AEA_AGENT
ARG AUTHOR

COPY start.sh /home/ubuntu
COPY install.sh /home/ubuntu

VOLUME /home/ubuntu/logs
WORKDIR /home/ubuntu

RUN aea init --reset --remote --ipfs --author ${AUTHOR}
RUN AEA_AGENT=${AEA_AGENT} bash install.sh

CMD ["start.sh"]

HEALTHCHECK --interval=3s --timeout=600s --retries=600 CMD netstat -ltn | grep -c 26658 > /dev/null; if [ 0 != $? ]; then exit 1; fi;
