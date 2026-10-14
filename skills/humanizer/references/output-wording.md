# Personal output wording policy

This is Muhammad Okfriansyah's explicit preference for every generated deliverable and completion message, including output produced with built-in, plugin, and supporting skills.

Do not emit `canonical`, any capitalization of it, or longer forms containing that spelling, including derived words and embedded identifiers. A source using the wording is evidence to interpret, not wording to repeat. The spelling is permitted only in this policy definition, checker configuration, negative test inputs, and immutable upstream evidence; those internal materials are not deliverable templates.

Choose wording from the meaning:

| Meaning | Write |
| --- | --- |
| Initial dataset and its manifest | Seed data |
| Main visual or engineering document | Design specification or engineering specification |
| Definition from which code is generated | Source schema or API definitions |
| Contracts, rules, or vocabulary shared by components | Shared contracts, conventions, or vocabulary |
| UUID text form | Lowercase, hyphenated UUID |
| Email identity transformation | Normalized email or email normalization |
| Stable bytes used for comparisons or hashing | Deterministic serialization |
| Required section or value order | Specified order |
| A reference file or version used by tooling | Source file or source version |

Remove redundant adjectives. Do not substitute one vague adjective everywhere. Preserve all technical behavior: byte ordering, explicit null/omission, identity, cryptography, precision, escaping, authorization, and externally defined formats.

Rename project-owned identifiers only when the task authorizes it, updating their consumers and references together. Do not silently rename required third-party keys or protocol literals. Omit an optional extension only when its absence is supported and does not lose required behavior; otherwise resolve the conflict with the user before delivering or externally publishing the artifact. Never hide the spelling with escapes, split strings, lookalike characters, or image text to evade the check.

## Required final check

Check complete generated text, including headings, captions, tables, code blocks, diagram labels, artifact names, and completion text. This check is required after supporting skills return and before handing off, exporting, publishing, or sending output.

```bash
python3 scripts/check_output_wording.py /absolute/path/to/deliverable
```

The checker accepts multiple files or directories. With no paths, or with `-`, it reads UTF-8 text from stdin; use this to check completion text without creating a project file. It is read-only: exit 0 means clean, exit 1 means wording must be rephrased, and exit 2 means input was not fully inspectable. Fix the problem and rerun; an input error is not a pass.

For PDF, Office, and other binary documents, extract all relevant authored text with the existing artifact tools and pass it through stdin or a temporary text file. Include names and captions, and inspect rendered image text through the artifact's normal visual review. Do not report a scan of binary bytes or an uninspected image as a text check. The directory scan skips known image/font/audio/video assets, filesystem metadata, and dependency caches; SVG and other authored text remain checked. Symlinked inputs require the actual output path.

Keep intermediate check data outside project deliverables. Check the final proposed completion text as well as the artifact. If a checker is unavailable, inspect the full output with an equivalent case-insensitive search and state the validation limitation. Instructions are personal defaults; the user's later explicit instructions and higher-priority constraints govern.
