# Architecture options

Compare ownership, change/deploy coupling, consistency, failure isolation, team operation and workload needs. Team size alone does not select architecture.

| Option | Useful property | Cost to examine |
| --- | --- | --- |
| Single deployable with cohesive modules | Local transactions and simple operations | Shared release/resource boundary |
| Separate services | Independent ownership/release/resource boundaries | Network failure, cross-service consistency and operation overhead |
| Asynchronous work | Durable deferred effects and caller decoupling | Delivery, ordering, replay, backpressure and recovery |
| Separate read/write models | Different query/write needs | Synchronization, staleness and extra ownership |
| Managed/event-triggered execution | Outsourced operation or burst handling | Platform constraints, cost and state lifetime |

Select only a pattern that addresses an established requirement. A broker, saga, event store, cache or extra service needs a concrete purpose. Describe success and failure interaction before selecting infrastructure. Diagrams show actual selected or explicitly proposed components, not a stock topology.
