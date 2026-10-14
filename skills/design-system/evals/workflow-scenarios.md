# Workflow review scenarios

Use these cases when revising the orchestrator. They check decision behavior beyond the structural checker; they do not replace an actual generation/rendering run.

| Input and existing context | Required behavior | Failure to catch |
|---|---|---|
| Create a package using an already approved identity | Reuse that identity; author one specification and linked mockup package; make routine refinements within the selection | Reopen palette approval or generate unsolicited alternatives |
| Combine proposal A as dark and proposal C as light | One design specification, shared token authority and component contracts, two theme overrides and one mockup gallery | Deliver two systems or keep the unused proposal as an active output |
| Create a package with no selected visual identity | Show one realistic visual proposal, explain meanings/tradeoffs in plain language, and obtain owner selection before adoption | Silently fix the identity or create three options by default |
| Compare three explicitly requested alternatives | Compare three provisional directions outside the final handoff; obtain selection; consolidate the selected direction into one package | Treat all proposals as approved systems or retain obsolete generated material in the final handoff |
| A state has its own hidden flag cleared, but is inside a hidden parent | Static nesting check fails for declared independent states; rendered review also checks ancestor visibility and actual layout/content | Claim success merely because the anchor exists or its own hidden flag is false |
| A native/game package has image storyboards and no browser runtime | Keep visuals under mockup/, document input/runtime limits, and verify annotations without requiring HTML/CSS or selecting an engine | Build an unsolicited application just to satisfy a web-only checklist |

Review outcome for revision 2.1.0: all six cases were traced through the updated instructions and contract. The checker regressions exercise layout, coverage, and nesting. No fresh end-to-end model generation or browser rendering is claimed for this skill-only revision.
