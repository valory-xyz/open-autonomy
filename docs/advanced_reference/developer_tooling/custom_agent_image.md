When building the agent images, you might run into a situation where an agent dependency requires a third party developer library which can lead to the image build failing. In such cases you can use a custom `Dockerfile` with a layer which installs this third party library. Use following template to define the `Dockerfile`

```dockerfile
ARG AUTONOMY_IMAGE_VERSION="latest"
ARG AUTONOMY_IMAGE_NAME="valory/open-autonomy"
FROM ${AUTONOMY_IMAGE_NAME}:${AUTONOMY_IMAGE_VERSION}

ARG AEA_AGENT
ARG AUTHOR
ARG EXTRA_DEPENDENCIES

RUN aea init --reset --remote --ipfs --author ${AUTHOR}

WORKDIR /root

# Install the third party libraries here

RUN AEA_AGENT=${AEA_AGENT} EXTRA_DEPENDENCIES=${EXTRA_DEPENDENCIES} bash /root/scripts/install.sh

CMD ["/root/scripts/start.sh"]

HEALTHCHECK --interval=3s --timeout=600s --retries=600 CMD netstat -ltn | grep -c 26658 > /dev/null; if [ 0 != $? ]; then exit 1; fi;
```

When building the image use, `--dockerfile` flag to point to this custom `Dockerfile`

```bash
$ autonomy build-image --dockerfile DOCKERFILE_PATH
```