# Cloud Deployment Introduction 

We have provided a number of ways to run the valory stack across multiple different cloud providers.

The deployment has been implemented using a minimal distribution of kubernetes to run as close to the bare metal as allowable. 

This approach leads to a number of key benefits for node operators & infrastructure providers.

1. No reliance upon an individual provider. We currently provide coverage for both Digital Ocean and for AWS.
2. Lower costs compared to using a managed alternative.
3. Easily portable cross cloud providers.

We have 3 deployment options available for external operators.
- docker-compose - This approach is advised for beginners less experienced users.
- Kubernetes Cluster - We provide full deployments for kubernetes
    - Single Node - This deployment approach is recommened for individual applications.
    - Multi Node - This deployment approach is recommened for more advanced users looking to run multiple agent nodes or applications.

Infrastructure deployment is handled by terraform to ensure replicatability across multiple providers whilst allowing external operators to configure the deployments to match their specific deployment requirements

# Pre-requisites

We require a domain for our cluster. This allow us to route traffic to our cluster controller node. This is a pre-requisite of both kubernetes based deployments, however the docker-compose deployment is able to skip this step.

The domain can be aquired from a domain registrar such as [goDaddy](https://www.godaddy.com), or [Freenon](https://www.freenom.com). Most cloud providers also offer this as a service such as AWS. The key requirement is to be able to update the domain registrars NameServer (NS) records easily.

##Install depenencies.

- [Skaffold](https://skaffold.dev/docs/install/): Deployment Orchestration
- [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation): Local Cluster deployment and management.
- [Kubectl](https://kubernetes.io/docs/tasks/tools/): kubernetes cli tool.
- [Docker](https://docs.docker.com/get-docker/): Container backend.
- [Terraform](https://www.terraform.io/downloads.html): Infrastructure management as code.



#Step-by-step Deployment Instructions

1. Acquire the external operator code.
```bash
git clone git@github.com:valory-xyz/external-node-operators.git
```



## Digital Ocean
1. We need to first create an authentication file to be used by terraform to create cloud resources. This can be done from the [API Settings](https://cloud.digitalocean.com/account/api/tokens). Save this
2. Once and


## AWS
### 
2. Login to AWS console.


