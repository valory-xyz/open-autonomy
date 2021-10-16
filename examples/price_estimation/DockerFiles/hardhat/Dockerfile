from node:16.7.0
WORKDIR /home/ubuntu/build
run git clone https://github.com/gnosis/safe-contracts.git
RUN cp -r /home/ubuntu/build/safe-contracts/* /home/ubuntu/build
run rm -r safe-contracts
run yarn install

