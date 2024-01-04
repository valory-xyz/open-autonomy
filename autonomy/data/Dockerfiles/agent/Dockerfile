ARG AUTONOMY_IMAGE_VERSION="latest"
ARG AUTONOMY_IMAGE_NAME="valory/open-autonomy"
FROM ${AUTONOMY_IMAGE_NAME}:${AUTONOMY_IMAGE_VERSION}

ARG AEA_AGENT
ARG AUTHOR
ARG EXTRA_DEPENDENCIES

RUN aea init --reset --remote --ipfs --author ${AUTHOR}

WORKDIR /root

RUN AEA_AGENT=${AEA_AGENT} EXTRA_DEPENDENCIES=${EXTRA_DEPENDENCIES} bash /root/scripts/install.sh

CMD ["/root/scripts/start.sh"]

HEALTHCHECK --interval=3s --timeout=600s --retries=600 CMD netstat -ltn | grep -c 26658 > /dev/null; if [ 0 != $? ]; then exit 1; fi;
