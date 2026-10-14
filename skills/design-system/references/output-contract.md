# Output contract

The user can override location or format. New packages use the standard layout below. Existing v1/v2 packages remain checkable with the legacy layout; the coverage schema version and directory layout are separate concerns.

```text
docs/design-system/
  design-system.md
  index.md
  components.md
  tokens.json
  coverage.json
  mockup/
    index.html                 # web gallery
    components.html            # web component catalog
    tokens.css                 # whenever HTML previews exist
    <screen-or-flow>.<html|png|jpg|webp|svg|md|mp4|webm>
    <local styles and scripts>
    assets/<artwork, icons, fonts, provenance, useful captures>
```

All visual artifacts and their supporting resources belong under singular `mockup/`. Native/game packages need no HTML wrapper, CSS, framework build, or engine project; use linked images and annotated storyboards when no native renderer is available. Optional HTML previews consume `mockup/tokens.css`, irrespective of the production target. Create directories only for actual content.

Additional root documents/data, such as readable coverage or measured contrast, must serve the current handoff. Keep validation and technical-design boundaries in `design-system.md`; separate `verification.md` and `remaining-work.md` are not default outputs. Keep generators, bulk test captures, and provisional comparisons outside the final package. After selection, remove obsolete artifacts created during this run; preserve pre-existing user work unless cleanup is authorized. Keep only useful actual captures, with provenance, alongside the mockup assets.

Keep review resources local. Browser demonstrations use fixture data and run from a static server without a production build; label simulated outcomes. An image/storyboard illustrates layout and behavior but does not demonstrate responsive transitions or runtime interaction. Formats cannot silently change the target technology.

## Design specification

`design-system.md` starts by explaining its use alongside the governing requirements for technical-document creation: requirements own scope/acceptance, while this specification owns the approved visual and visible-interaction contracts. It provides source version/status and evidence, scope/roles/player context, target decision table, visual direction, identity/voice, typography, contrast roles, spacing/layout/density, shape/elevation, icons/artwork, motion/feedback, components and consequential states. Explain navigation, input/accessibility behavior and relevant platform adaptations, with links to real visual artifacts and requirement/acceptance references. Identify assumptions, recommendations and unresolved choices separately from adopted decisions. Include handoff/export mappings only for declared technologies. Show color meanings, visible swatches, permitted/prohibited combinations and measured contrast, typography through realistic content, and components through usable visual examples. Identify authentication/session and other account states when required by the product; do not add accounts to products that do not need them. Record validation in a substantive `## Validation and handoff` section (a longer heading beginning with those words is accepted): checks/methods/results, actual limitations, and engineering responsibilities. A heading or template placeholder alone is not a completed specification.

The component catalog shows anatomy, variants, states and appropriate context. Markdown catalogs embed actual visuals or link clearly labeled component demonstrations; prose alone is not a visual catalog. Images/storyboards identify the tokens and variants they depict so manual review can reconcile them. Multi-platform packages share one core, with justified target overrides. Themes are variants of this same system, not duplicate systems. Record owner selection and rationale; no particular project palette, font, theme count, or product feature is a universal default.

## Tokens and exports

Use flat keys within primitive → semantic → component layers:

```json
{
  "primitive": {"color-neutral-950": "#111111", "space-4": 16},
  "semantic": {"surface-canvas": "{primitive.color-neutral-950}", "space-content": "{primitive.space-4}"},
  "component": {"card-background": "{semantic.surface-canvas}"},
  "overrides": {"phone": {"semantic": {"space-content": 20}}}
}
```

Strings/numbers are supported leaf values; aliases are `{layer.token-name}`. Numeric units and typography/color representations are documented in the specification; neutral values need not be CSS strings. `overrides` is optional, keyed by declared target IDs, and replaces existing base keys within those layers. Aliases resolve against the effective base plus target overrides. Shared and overridden sets must have valid references without cycles.

CSS is a web/preview export, exposing matching `--layer-token-name` properties with `var()` aliases. Default literals use the same JSON values; unit conversion or other intentional representation changes use an optional `css_values` object in tokens.json, mapping `layer.token-name` to an exact CSS literal (for example `primitive.space-4: "16px"`). For target overrides, prefix a conversion key with the target ID and `/`, for example `phone/semantic.space-content: "20px"`. Such conversions must be documented. Alias conversions remain aliases. Export target CSS overrides for targets represented by HTML, or when otherwise explicitly provided; native/image-only targets in mixed packages need no CSS overrides. Target CSS overrides live in the same export under `[data-design-target="phone"]` selectors so the checker can reconcile them with JSON overrides. Every HTML artifact consumes `tokens.css` directly or through a local stylesheet importing it. Apply the declared target attribute to preview roots needing overrides.

Native/engine exports are optional and require declared technology, documented units/mappings and consistency with tokens.json. No native programming language is selected solely to export tokens. Static visual token use and target attribute behavior still need manual inspection; structural validation checks references/exports, not raster pixels or effective styling.

## Coverage v2

New packages use `schema_version: 2`. The existing v1 HTML/FR/AC format remains accepted without regeneration. Example for a mobile image:

```json
{
  "schema_version": 2,
  "source": {"path": "../PRD.md", "sha256": "<digest of source bytes>"},
  "targets": [{"id": "phone", "platform": "mobile", "product_type": "application"}],
  "screens": [{
    "id": "catalog", "title": "Catalog", "format": "image", "file": "mockup/catalog.png",
    "targets": ["phone"], "roles": ["Viewer"], "requirements": ["FR-001"], "acceptance": ["AC-001"],
    "render_contexts": ["Portrait phone; dimensions and units in annotations"],
    "states": ["ready"],
    "state_locations": {"ready": {"file": "mockup/catalog.png", "label": "Ready", "annotation": "mockup/catalog-notes.md#ready"}}
  }],
  "requirements": [{"id": "FR-001", "disposition": "visual", "screens": ["catalog"]}],
  "acceptance_criteria": [{"id": "AC-001", "disposition": "visual", "locations": ["mockup/catalog-notes.md#ready"]}]
}
```

Use actual roles, IDs and contexts. Target platforms are `web`, `mobile`, `desktop`, `console`, or `unspecified`; product types are `application`, `game`, or `unspecified`. Detailed OS/hardware/input/technology decisions belong in the source-backed table. A mobile game uses mobile platform plus game product type. Both kinds of guidance apply. Empty/unknown values are not guessed.

Screen formats:

- `html`: package `.html` file, positive integer `viewports` in CSS pixels, state locations as real `#id` fragments. Optional render_contexts add orientation/input context.
- `image`: package PNG/JPEG/WebP/GIF/SVG file; nonempty render_contexts and each state's `{file, label, annotation}` location.
- `storyboard`: package Markdown file with local linked/embedded image/video visuals and annotations; nonempty render_contexts and object state locations.
- `preview`: supplied package image/video capture (MP4/WebM/MOV also supported); nonempty render_contexts and object state locations. Specify time/frame or capture context in the annotation when applicable.

For non-HTML states, `file` identifies an existing nonempty visual or storyboard; `label` must appear in the section identified by `annotation`, a package Markdown file with an explicit HTML ID anchor such as `<a id="ready"></a>`. Embed/link the identified visual in that section. Do not force images into HTML wrappers or claim that naming a state proves its behavior. A storyboard must contain actual visual references. All artifact/annotation links stay inside the package; the design specification may cite the declared primary or supporting sources outside it. Ordinary Markdown heading links are supported; state annotations use explicit anchors.

Each screen identifies declared targets, source requirements, acceptance references, roles/player context, and inspectable states. Each functional source requirement appears exactly once with `visual`, `cross-cutting`, `technical`, or `deferred` disposition. Visual/cross-cutting entries reference screens; technical/deferred entries explain why no screen is appropriate. Screen/requirement mappings agree. Acceptance references must exist in the source; missing semantic/exceptional coverage cannot be relabeled technical just to pass.


For standard packages, also provide `quality_requirements` and `acceptance_criteria` disposition arrays whenever the source defines those IDs. Each entry has `id`, `disposition`, and either nonempty `screens` (inventory IDs) or `locations` (package-relative declared visual/state links) for visual/cross-cutting obligations; technical/deferred entries have specific `notes`. Reconcile each source ID exactly once. Do not repeat fixed requirement counts from a prior product. Legacy packages may omit these arrays; when supplied, they are validated.

For example, `{"id":"AC-001","disposition":"visual","locations":["mockup/catalog.html#ready"]}` maps to the actual declared state. `{"id":"NFR-001","disposition":"technical","notes":"Storage durability requires service and database tests; this package specifies only visible recovery outcomes."}` explains a nonvisual obligation. Images/storyboards can reference their declared file or state annotation instead of an HTML fragment.

## Sources other than FR/AC tables

The checker automatically reads all `FR-NNN`, `NFR-NNN`, and `AC-NNN` definition rows from the primary source, preserving current PRD behavior. Use `--source <document>` or its existing `--prd` alias; source.path must identify that file and sha256 must match its current bytes. When additional governing documents supply decisions, add optional `source.supporting_documents: [{"path": "../decisions.md", "sha256": "<digest>"}]`; cite them in the specification. Their digests are checked, while requirement extraction remains tied to the primary source.

For a GDD/brief without those tables, provide `source.requirements` and, where defined, `source.quality_requirements` and `source.acceptance` objects mapping stable IDs to exact nonempty source excerpts. Reuse existing IDs where available; otherwise explicitly label local traceability IDs in the specification without inventing new behavior. The checker verifies excerpts exist in the source and mappings agree. If FR/NFR/AC definition rows exist, explicit IDs must match the complete corresponding table set. An empty acceptance list is allowed only when the source has no acceptance definitions; record that limitation. Source extraction completeness and meaning still need manual reconciliation.

## Indexes and handoff

`index.md` begins with a link to `design-system.md`, then the governing source and supporting artifacts. It links every screen/flow and consequential state with roles/targets. Web `mockup/index.html` makes the specification its first document link and a prominent primary action; skip links and same-page navigation may precede it. It also reaches the visual component catalog and every screen. Keep both indexes consistent, and component examples and annotation files reachable.

Source citations may link from the specification and standard indexes to the exact primary/supporting documents declared in coverage. Other external filesystem links remain invalid; source citations do not permit remote runtime dependencies.

Run the checker with `--layout standard` for new packages. The default `auto` detects `mockup/`; otherwise it uses legacy layout. `--layout legacy` retains root HTML/CSS and standalone verification expectations for older packages without rewriting them. An explicitly customized contract needs adapted checks and a truthful validation limitation.

The final handoff links the specification first, then the gallery and necessary supporting files. State the adopted direction, validation outcome, and material limitations. A technical-design responsibility is not evidence of unfinished design work; missing requested visual coverage is.
