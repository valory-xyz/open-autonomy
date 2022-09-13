# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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


HARDHAT_TEMPLATE: str = """apiVersion: apps/v1
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
          image: %s:%s
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


CLUSTER_CONFIGURATION_TEMPLATE: str = """apiVersion: batch/v1
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
        image: {tendermint_image_name}:{tendermint_image_version}
        command: ['/usr/bin/tendermint']
        args: ["testnet",
         "--config",
         "/etc/tendermint/config-template.toml",
         "--o",  ".", {host_names},
         "--v", "{number_of_validators}"
         ]
        volumeMounts:
          - mountPath: /tendermint
            name: nodes
      volumes:
        - name: nodes
          persistentVolumeClaim:
            claimName: 'nodes'
      restartPolicy: Never
  backoffLimit: 3
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: logs-pvc
spec:
  storageClassName: nfs-client
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1000M
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: tendermint-pvc
spec:
  storageClassName: nfs-client
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1000M
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: benchmark-pvc
spec:
  storageClassName: nfs-client
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1000M
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nodes
spec:
  storageClassName: nfs-client
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1000M
"""


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
        image: {tendermint_image_name}:{tendermint_image_version}
        imagePullPolicy: Always
        resources:
          limits:
            memory: "1512Mi"
            cpu: "1"
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
            value: "/logs/node_{validator_ix}.txt"
          - name: LOG_LEVEL
            value: {log_level}
        args: ["run", "--no-reload", "--host=0.0.0.0", "--port=8080"]
        volumeMounts:
          - mountPath: /tm_state
            name: persistent-data-tm
          - mountPath: /logs
            name: persistent-data
          - mountPath: /tendermint
            name: nodes

      - name: aea
        image: {runtime_image}
        imagePullPolicy: Always
        resources:
          limits:
            memory: "1512Mi"
            cpu: "1"
          requests:
            cpu: "0.05"
            memory: "128Mi"
        env:
          - name: HOSTNAME
            value: "agent-node-{validator_ix}"
          - name: CLUSTERED
            value: "1"
          - name: LOG_FILE
            value: "/logs/aea_{validator_ix}.txt"
          - name: PYTHONHASHSEED
            value: "0"
        volumeMounts:
          - mountPath: /logs
            name: persistent-data
          - mountPath: /benchmark
            name: persistent-data-benchmark
          - mountPath: /build
            name: nodes
          - mountPath: /agent_key
            name: agent-key
      volumes:
        - name: agent-key
          secret:
            secretName: agent-validator-{validator_ix}-key
            items:
            - key: private_key
              path: ethereum_private_key.txt
        - name: persistent-data
          persistentVolumeClaim:
            claimName: 'logs-pvc'
        - name: persistent-data-benchmark
          persistentVolumeClaim:
            claimName: 'benchmark-pvc'
        - name: persistent-data-tm
          persistentVolumeClaim:
            claimName: 'tendermint-pvc'
        - name: nodes
          persistentVolumeClaim:
            claimName: 'nodes'
"""

AGENT_SECRET_TEMPLATE: str = """
apiVersion: v1
stringData:
    private_key: '{private_key}'
kind: Secret
metadata:
  annotations:
  name: agent-validator-{validator_ix}-key
type: Opaque
"""
