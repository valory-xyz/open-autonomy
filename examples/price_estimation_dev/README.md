# ABCI development environment for Price Estimation Skill


### Preliminaries

Make sure you have installed on your machine:

- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Run a local demo

> To set up an environment

```
python3 create_env.py NUMBER_OF_AGENTS
```

> To build dev images and start N agents runtime.

```
make localnet-start-fresh
```

> To run agents with already existing dev images.

```
make localnet-start
```
