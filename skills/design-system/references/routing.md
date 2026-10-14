# Target resolution and supporting routes

## Resolve before routing

Record a decision table in the design specification: dimension, selected value or unspecified, source document/section, status, and rationale. Resolve product type, physical platforms, input methods, framework/native toolkit, frontend/native programming language, component library, and game engine independently. A web game can need both web and game guidance; a mobile game can need both mobile and game guidance.

Use explicit user instructions, then current governing product requirements, then adopted project decisions, then this output contract, then supporting recommendations. Existing implementation can inform a handoff but must not silently supersede approved requirements. Resolve clear supersession; ask about an unresolved material conflict instead of choosing the most recently installed skill. Preserve each recommendation/open choice's status. Consult multiple governing documents where needed; the coverage source identifies the primary source and additional decisions cite their actual documents.

Examples:

| Evidence | Active guidance | Remains unresolved |
|---|---|---|
| No target specified | Shared foundations and neutral visual examples | Production platform, framework, language, library, engine |
| PRD requires Svelte/TypeScript web | Web; matching Svelte recommendations; optional Svelte component mapping | shadcn adoption unless selected |
| PRD requires React web | Web and a relevant available React adapter | Svelte routes stay inactive |
| Mobile with no toolkit | Mobile and relevant OS guidance if selected | Flutter/RN/SwiftUI/Compose stay unspecified |
| Flutter mobile | Mobile and matching Flutter guidance | Native-language/OS library assumptions |
| Kotlin backend only | Shared guidance for requested design | Frontend language/framework; backend Kotlin does not imply Compose |
| Game with unspecified engine | Game visual/interaction guidance | Unity/Godot/Unreal, engine language, runtime code |
| Declared game engine | Game plus relevant platform and available engine adapter | Languages/library choices not required by the engine documentation or user |
| Web and mobile | Shared core with justified target overrides | No automatic single-framework decision |

Do not install adapters speculatively. An actual target plus authorized installation can use skill-installer; verify its current entry point and preserve provenance. Without an adapter, create neutral contracts and document the missing handoff capability. External tools/services remain optional and subject to the user's authorization.

## General recommendations and foundations

Supporting entries live beside this skill in the personal skills root; resolve relative to the installed skill directory, not the project's working directory. General routes are `ui-ux-pro-max`, `design-system-foundations`, and applicable `impeccable` review references. Browser routes are `frontend-design` and `fixing-accessibility`. `shadcn-svelte` is a conditional technology adapter, not a required general dependency. Discover other task-relevant installed adapters from the current catalog.

For UI UX Pro Max, inspect `scripts/search.py --help` and use its actual flags. Request general recommendations without persistence initially. Pass `--stack` only when the declared technology has a matching supported option; otherwise omit it. A platform or HTML preview alone does not select `html-tailwind`, React, or any production framework. Design-system generation and stack search may be separate commands; follow the installed helper. Treat any generated implementation snippets as optional guidance, not selected dependencies. Keep intermediate outputs temporary rather than creating another authoritative package.

For foundations, reuse three-layer tokens and component/state patterns. Inspect helpers before invocation: legacy token schema/CSS generation may need temporary adapters. CSS is appropriate for browser artifacts; native/game exports need declared target mappings. Presentation generation and remote-image scripts are outside this route.

## Authoring and review

`frontend-design` leads web/browser demonstration authoring using shared tokens and source constraints. Its CSS/framework/aesthetic examples do not establish native/game implementation requirements. For image/storyboard/native/game authoring, use relevant available visual tools and selected platform guidance; renderer availability changes verification evidence, not production technology.

The installed `impeccable` is a scoped Codex review adapter. Use critique for hierarchy/usability and harden for relevant states. Web audit rules apply to web/browser artifacts. For selected Apple or Android targets, read `reference/ios.md`, `reference/android.md`, or `reference/audit.native.md` only as needed. Native build or framework suggestions are conditional on the declared target and available authorized tools. Shared hierarchy/craft principles can apply elsewhere; web/native playbooks are not a dedicated game-engine adapter. Keep the design specification instead of forcing root PRODUCT.md/DESIGN.md, upstream binaries, hooks, or services.

Use `fixing-accessibility` for actual HTML semantics, labels, form errors, keyboard/focus, dialogs, and color-independent feedback. Native/game accessibility uses target-appropriate review and runtime evidence; an HTML demo cannot establish native accessibility conformance.

## Conditional technology handoff

A technology-specific route needs a declared matching technology AND relevant implementation examples, component mapping, or handoff work. Use only the declared language in implementation examples; otherwise prefer pseudocode and neutral anatomy/behavior contracts. Separate frontend/native language from backend requirements.

For declared Svelte, `shadcn-svelte` can supply an optional mapping proposal. Read official component API documentation before detailed examples. Library adoption is a separate decision; a Svelte requirement alone does not commit shadcn. Documentation does not require running `init`, `add`, `update`, scaffolding a project, or editing production source. The same gates apply to other frameworks/toolkits/engines. Use source-backed conventions rather than inventing adapter capabilities.

A native or engine renderer is optional for documentation: images/storyboards can fulfill visual design coverage while runtime/input checks remain pending. Report precise missing capabilities without claiming an unavailable preview was exercised.
