# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Kubernetes Templates module."""

from deployments.constants import IMAGE_VERSION


HARDHAT_TEMPLATE: str = (
    """apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    io.kompose.service: hardhat
  name: hardhat
spec:
  replicas: 1
  selector:
    matchLabels:
      io.kompose.service: hardhat
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        io.kompose.network/localnet: "true"
        io.kompose.service: hardhat
    spec:
      containers:
        - args:
            - /usr/local/bin/yarn
            - run
            - hardhat
            - node
            - --port
            - "8545"
            - --hostname
            - "0.0.0.0"
          command:
            - /bin/bash
          image: valory/consensus-algorithms-hardhat:%s
          name: hardhat
          ports:
            - name: http
              containerPort: 8545
          resources: {}
          workingDir: /home/ubuntu/build
          imagePullPolicy: Always
      imagePullSecrets:
      - name: regcred
      restartPolicy: Always
status: {}
---
apiVersion: v1
kind: Service
metadata:
  labels:
    io.kompose.service: hardhat
  name: hardhat
spec:
  ports:
    - protocol: TCP
      port: 8545
      targetPort: 8545
  selector:
    io.kompose.service: hardhat
status:
  loadBalancer: {}
"""
    % IMAGE_VERSION
)


CLUSTER_CONFIGURATION_TEMPLATE: str = (
    """apiVersion: batch/v1
kind: Job
metadata:
  name: config-nodes
spec:
  template:
    spec:
      imagePullSecrets:
      - name: regcred
      containers:
      - name: config-nodes
        image: valory/consensus-algorithms-tendermint:%s
        command: ['/usr/bin/tendermint']
        args: ["testnet",
         "--config",
         "/etc/tendermint/config-template.toml",
         "--o",  ".", {host_names},
         "--v", "{number_of_validators}"
         ]
        volumeMounts:
          - mountPath: /tendermint
            name: build
      volumes:
        - name: build
          persistentVolumeClaim:
            claimName: 'build-vol-pvc'
      restartPolicy: Never
  backoffLimit: 3
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: logs-pvc
spec:
  storageClassName: nfs
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1000M
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: build-vol-pvc
spec:
  storageClassName: nfs
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1000M
"""
    % IMAGE_VERSION
)


AGENT_NODE_TEMPLATE: str = """apiVersion: v1
kind: Service
metadata:
  name: abci{validator_ix}
  labels:
    run: abci{validator_ix}
spec:
  ports:
  - port: 26656
    protocol: TCP
    name: tcp1
  - port: 26657
    protocol: TCP
    name: tcp2
  selector:
    app: agent-node-{validator_ix}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-node-{validator_ix}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: agent-node-{validator_ix}
  template:
    metadata:
      labels:
        app: agent-node-{validator_ix}
    spec:
      imagePullSecrets:
      - name: regcred
      restartPolicy: Always
      containers:
      - name: node{validator_ix}
        image: valory/consensus-algorithms-tendermint:%s
        imagePullPolicy: Always
        resources:
          limits:
            memory: "512Mi"
            cpu: "0.5"
          requests:
            cpu: "0.05"
            memory: "128Mi"
        ports:
          - containerPort: 26656
          - containerPort: 26657
        workingDir: /tendermint
        env:
          - name: HOSTNAME
            value: "node{validator_ix}"
          - name: ID
            value: "{validator_ix}"
          - name: PROXY_APP
            value: tcp://localhost:26658
          - name: TMHOME
            value: /tendermint/node{validator_ix}
          - name: CREATE_EMPTY_BLOCKS
            value: "true"
          - name: LOG_FILE
            value: "logs/logs/node_{validator_ix}_logs.txt"
        args: ["run", "--no-reload", "--host=0.0.0.0", "--port=8080"]
        volumeMounts:
          - mountPath: /logs
            name: logs
          - mountPath: /tendermint
            name: build

      - name: aea
        image: valory/consensus-algorithms-open-aea:%s
        imagePullPolicy: Always
        resources:
          limits:
            memory: "512Mi"
            cpu: "0.5"
          requests:
            cpu: "0.05"
            memory: "128Mi"
        env:
          - name: HOSTNAME
            value: "agent-node-{validator_ix}"
          - name: CLUSTERED
            value: "1"
          - name: LOG_FILE
            value: "logs/logs/aea_{validator_ix}_logs.txt"
        volumeMounts:
          - mountPath: /logs
            name: logs
          - mountPath: /build
            name: build
      volumes:
        - name: logs
          persistentVolumeClaim:
            claimName: 'logs-pvc'
        - name: build
          persistentVolumeClaim:
            claimName: 'build-vol-pvc'
""" % (
    IMAGE_VERSION,
    IMAGE_VERSION,
)
