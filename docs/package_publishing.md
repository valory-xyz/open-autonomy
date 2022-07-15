# Package publishing

Developers, node operators and service owners interact with each other through the onchain protocol to register components, agents and services. Let's see how this all works since
a component inception to a service deployment.

The first step begins with a developer creating some cool code that does something valuable. This developer creates a software package with the {{open_autonomy}}
framework. This package, that we know as component, contains not only the code but also its configuration and dependencies (```component.yaml``` in the image). Once the package is completed,
it needs to be pushed to IPFS registry so other people can access to it. Using the ```autonomy``` CLI a developer can perform this action, and an IPFS hash that
points to this unique code will be returned.

<figure markdown>
![](./images/create_component.svg)
<figcaption>A developer creates a component and pushes it to the IPFS registry</figcaption>
</figure>

Now it's time to register the component in the onchain protocol so other people can find it. Using the protocol frontend, the developer must fill a form with
the details of the package, like its IPFS hash, its owner address, description and so on. Once every detail has been filled out, the frontend will generate a ```json```
file with all the metadata, push it to IPFS and retrieve the corresponding hash. After this, that hash will be registered on the onchain protocol and the component
owner will receive in his wallet an NFT that represents the ownsership of this component. It's important to emphasize that two different pushes to IPFS have been
performed up to this point: the first one, done by the developer to push the code and a second one done by the frontend to push the metadata (that contains the code hash itself).

<figure markdown>
![](./images/register_component.svg)
<figcaption>A developer registers a component into the protocol</figcaption>
</figure>

At some point, a service owner might want to use our useful component in their service. In an analogous way to how a component was registered, this service owner
registers a service, specifying all its components as well as the number of agents that will run the service. A NFT will be minted as well and sent to the owner wallet.

<figure markdown>
![](./images/register_service.svg)
<figcaption>A service owner registers a service into the protocol</figcaption>
</figure>

Now a node operator sees this newly minted service in the protocol frontend, and finds it interesting, so he/she decides to run one or more agents for that service.
Once again, this agent is registered using the service id and a NFT is minted as well.

<figure markdown>
![](./images/register_agent.svg)
<figcaption>An operator registers an agent into the protocol</figcaption>
</figure>

Every piece is in place now. The only remaining thing is actually spinning up the service. Node operators run their agents using the ```autonomy``` CLI, the agents
form a network and the service is stablished. This service can be monetized and the revenue generated from the service users will be distributed among the component creators, service owners, node operators and the onchan protocol itself.

<figure markdown>
![](./images/run_service.svg)
<figcaption>An operator runs an agent that forms part of a service</figcaption>
</figure>