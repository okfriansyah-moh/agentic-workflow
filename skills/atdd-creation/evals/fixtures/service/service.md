# Delivery dispatch service — accepted contract

The chosen stack is Go, gRPC and PostgreSQL. This is an internal service with no browser or UI, assistant, file upload or payment flow. A dispatcher submits delivery jobs; workers claim and complete them.

- DSP-1: A caller authenticated for tenant A cannot read or submit tenant B's jobs; permission-denied responses reveal no B job fields and make no B state changes.
- DSP-2: Within a tenant, a submit request key is unique. Same key and same destination body returns the original job ID without a second job; same key and different body returns already-exists without changing the original. The rule holds for concurrent calls and after a committed submission whose response was lost.
- DSP-3: A successful submission stores the queued job and its audit event in one transaction. If either insert fails, neither is committed and submission reports failure.
- DSP-4: A worker claim grants a 30-second lease. At most one active lease owner exists. After a worker crash, another worker may claim once the lease expires. A late result from the old lease cannot complete the job.
- DSP-5: Transient provider failures are retried at most three attempts total. After the third failure the job is permanently failed with its attempt history retained. Restarting a worker retains the durable attempt count. A success stops further attempts.
- DSP-6: If the caller's deadline expires before submission commits, the transaction is rolled back. If the reply is lost after commit, a subsequent same-key call follows DSP-2; the caller must not infer a rollback from a lost reply.
- DSP-7: Dispatch should be fast at production load. The latency budget, load model and resource ceiling remain undecided and require an owner decision.

All acceptance cases are to be planned; no executed evidence has been provided. Real RPC deadlines, database transactions, lease contention and restart boundaries require later integration evidence. Simulated provider failures must be labeled as simulation.

Verification commitment: include isolated unit cases for tenant/key binding and failure/attempt-limit decisions, alongside the required real RPC/PostgreSQL cases. Setup for those real boundaries is a future execution prerequisite, not an unknown expected outcome. A deployment endpoint/credential value is provided by the later isolated test environment; its absence does not create a new permission policy. DSP-7 still lacks a consequential performance contract.
