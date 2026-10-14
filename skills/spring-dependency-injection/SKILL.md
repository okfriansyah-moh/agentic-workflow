---
name: spring-dependency-injection
description: "Implement or review Spring bean wiring, constructor injection, qualifiers and lifecycle without dependency cycles."
metadata:
  version: "1.0.0"
---

# spring-dependency-injection

Use the project's Spring version and existing module boundaries. Distinguish ordinary object construction from container-managed collaborators before adding annotations.

Prefer constructor injection for required dependencies and immutable fields. A single constructor normally does not need `@Autowired`; use explicit constructor selection only when the class has multiple candidates and the intent is unambiguous. Use parameter qualifiers for genuinely distinct implementations rather than an unexplained global primary bean. Optional dependencies must be truly optional and have tested absence behavior.

Place interface contracts at the consuming boundary when that fits the architecture. Wire concrete adapters at the composition boundary. Avoid field injection, service locators and static container access because they hide required dependencies. Keep configuration properties typed and validated at startup.

Treat a constructor cycle as a design defect: identify the shared responsibility, move the interface or split orchestration from domain behavior. `@Lazy`, provider indirection or enabling circular references does not resolve a prohibited dependency cycle. Deferred lookup is appropriate only for a real lifecycle/scope requirement with documented behavior.

Inspect bean scope and thread safety. Singleton services must not hold request state; scoped proxies need an actual lifetime requirement. Startup callbacks should perform bounded initialization and fail clearly on invalid required configuration. Resource ownership includes shutdown cleanup.

Verify wiring with a focused context test that uses the production configuration where applicable, plus an architecture/dependency cycle check. Unit tests construct classes directly. Negative fixtures should fail for ambiguous beans and forbidden cycles; a successful mock-only unit test is insufficient wiring evidence. Return the dependency path, design decision and actual verification.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.
