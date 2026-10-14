# System design coverage

Use the parent document contract when supplied. Cover context/goals, constraints/source decisions, components and ownership, data, contracts, significant runtime scenarios, deployment/configuration, quality/security, failure/recovery, decisions/alternatives and verification.

Use C4 context/container concepts and focused component/sequence/state diagrams as needed. Keep component and operation names consistent across diagrams and contracts. Describe future-state design explicitly when code does not yet exist.

Define each consequential operation's authorized caller, inputs, validation, atomic effect, response/error and uncertain outcome. Explain resource and consistency boundaries before choosing scaling mechanisms. Keep interfaces and ownership concrete enough for implementation and later test derivation. Embed artifacts into the user's document when a single output is requested.
