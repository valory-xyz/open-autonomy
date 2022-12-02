FROM alpine:3.7
MAINTAINER Valory AG

ENV TENDERMINT_VERSION=0.34.19

RUN apk update && \
    apk upgrade && \
    apk --no-cache add curl jq file net-tools \
    python3 bash py3-pip

RUN wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh &&\
    chmod u+x wait-for-it.sh &&\
    mv wait-for-it.sh /usr/local/bin

# Download Tendermint
RUN curl -L https://github.com/tendermint/tendermint/releases/download/v${TENDERMINT_VERSION}/tendermint_${TENDERMINT_VERSION}_linux_amd64.tar.gz > tendermint.tar.gz &&\
    tar -xf tendermint.tar.gz &&\
    mv tendermint /usr/bin &&\
    rm -fr tendermint.tar.gz

RUN mkdir -p /app /tm_state

COPY app.py /app/
COPY tendermint.py /app/

WORKDIR /app
RUN pip3 install Flask==2.0.2 requests==2.27.1 Werkzeug==2.0.3


VOLUME /tendermint
VOLUME /tm_state

EXPOSE 26656 26657

ENV FLASK_APP=/app/app.py:create_server
ENV FLASK_ENV=production

STOPSIGNAL SIGTERM
WORKDIR /tendermint

COPY wrapper.sh /usr/bin/wrapper.sh
COPY config-template.toml /etc/tendermint/config-template.toml

RUN chmod 777 -R /app
RUN chmod 777 -R /tendermint
RUN chmod 777 -R /tm_state


ENTRYPOINT ["/usr/bin/flask"]
CMD ["run", "--no-reload", "--host=0.0.0.0", "--port=8080"]

HEALTHCHECK --interval=3s --timeout=600s --retries=600 CMD netstat -ltn | grep -c 26657 > /dev/null; if [ 0 != $? ]; then exit 1; fi;
