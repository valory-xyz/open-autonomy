# Deploy the service

The last step in the [development process](../overview_of_the_development_process.md) consists in deploying the service. There are several ways how you can deploy a service, depending on its current status, ranging from local, testing deployments to cloud deployments of production services.

<figure markdown>
![](../../images/development_process_deploy_service.svg)
<figcaption>Part of the development process covered in this guide</figcaption>
</figure>

!!! warning "Important"

    If your service is stored in a local registry, we recommend that you fetch it outside the registry (to an independent service runtime folder) before you start with the deployment process. This is to avoid publishing unintended files (e.g., temporary files or private keys) on the remote registry.

## What you will learn

This guide covers step 6 of the [development process](../overview_of_the_development_process.md). You will learn the different types of service deployment offered by the framework.

You must ensure that your machine satisfies the [framework requirements](../set_up.md#requirements), you have [set up the framework](../set_up.md#set-up-the-framework), and you have a local registry [populated with some default components](../set_up.md#populate-the-local-registry-for-the-guides). As a result you should have a Pipenv workspace folder with an initialized local registry (`./packages`) in it.

## Types of deployment

The framework allows to deploy services in a variety of ways. Namely, there are three aspects of the deployment that you need to decide:

**Local vs. cloud deployment:**
  : abcd

**Manual vs. automatic deployment:**

  : abcd

**Docker Compose vs. Kubernettes deployment:**

  : abcd
