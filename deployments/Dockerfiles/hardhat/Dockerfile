from node:16.7.0
WORKDIR /home/ubuntu/build
run git clone https://github.com/valory-xyz/safe-contracts
WORKDIR /home/ubuntu/build/safe-contracts
run git checkout feat/london-hardfork
WORKDIR /home/ubuntu/build
RUN cp -r /home/ubuntu/build/safe-contracts/* /home/ubuntu/build
run rm -r safe-contracts
run yarn install
ENTRYPOINT ["/usr/local/bin/yarn"]
CMD ["run", "hardhat", "node", "--port", "8545"]
