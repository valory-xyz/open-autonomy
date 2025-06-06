from node:16.7.0
WORKDIR /home/ubuntu/build
RUN git clone https://github.com/safe-global/safe-smart-account
WORKDIR /home/ubuntu/build/safe-smart-account
RUN git checkout v1.3.0
WORKDIR /home/ubuntu/build
RUN cp -r /home/ubuntu/build/safe-smart-account/* /home/ubuntu/build
RUN rm -rf safe-smart-account
run yarn install
ENTRYPOINT ["/usr/local/bin/yarn"]
CMD ["run", "hardhat", "node", "--port", "8545"]
