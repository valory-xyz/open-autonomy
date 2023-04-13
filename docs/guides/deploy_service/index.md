# Deploy the service

The last step in the [development process](../overview_of_the_development_process.md) consists in deploying the service. There are several ways how you can deploy a service, depending on its current status, ranging from local, testing deployments to cloud deployments of production services.

<figure markdown>
![](../../images/development_process_deploy_service.svg)
<figcaption>Part of the development process covered in this guide</figcaption>
</figure>



## What you will learn

This guide covers step 6 of the [development process](../overview_of_the_development_process.md). You will learn the different types of service deployment offered by the framework.

You must ensure that your machine satisfies the [framework requirements](../set_up.md#requirements), you have [set up the framework](../set_up.md#set-up-the-framework), and you have a local registry [populated with some default components](../set_up.md#populate-the-local-registry-for-the-guides). As a result you should have a Pipenv workspace folder with an initialized local registry (`./packages`) in it.

## Types of deployment

You need to consider the following three aspects when deploying an agent service:

**Local vs. cloud deployment:**
  : Local deployment on machines managed locally, or deployment on a cloud provider (currently supported for Amazon Web Services (AWS) and Digital Ocean).

**Manual vs. automated mode:**
  : Manual mode require that the user executes explicitly all the steps to deploy a service (fetch the service, build agent images, build the deployment, run the service) and configure a number of parameters. Automated mode takes care of executing these tasks with little input from the user. Automated mode is only available for services minted in the [Autonolas Protocol](https://docs.autonolas.network/protocol/).

**Docker Compose vs. Kubernetes cluster:**
  : These are the two deployment automation technologies currently supported.

!!! example

    If you are developing an agent service and want to test locally, then you should execute a local, manual deployment based on Docker Compose.
