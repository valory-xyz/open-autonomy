FROM valory/open-autonomy:latest

COPY run.sh /home/ubuntu
WORKDIR /home/ubuntu
RUN aea init --reset --remote --ipfs --author default_author
CMD ["run.sh"]
HEALTHCHECK --interval=3s --timeout=600s --retries=600 CMD netstat -ltn | grep -c 26658 > /dev/null; if [ 0 != $? ]; then exit 1; fi;