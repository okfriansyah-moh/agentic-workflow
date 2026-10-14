# Conditional platform and game guidance

Read only the branches needed by the documented targets. Combine shared foundations with justified platform variants, rather than cloning unrelated design systems. Platform-specific units, typography metrics, density, input and accessibility rules need explicit mappings; browser pixels do not automatically equal native points, density-independent units, or engine units.

## Web and browser demonstrations

Specify responsive layout/navigation, information hierarchy, content overflow, keyboard/focus behavior, semantic controls, dialogs and browser state feedback. Demonstrate consequential states at chosen viewport widths. HTML used to review a mobile/game design remains a browser simulation; label what touch, native navigation or controller behavior it cannot prove.

## Mobile applications

Resolve OS/device classes and orientation only from scope; a mobile requirement alone does not choose a toolkit or both operating systems. Specify native navigation/back behavior, safe areas/insets, touch targets, gesture discoverability and alternatives, keyboard obstruction, adaptive layout, text scaling and readable truncation. Include permissions, interruption, connectivity, restoration, or device-specific states where the source behavior needs them. Distinguish native screen-reader/input verification from an annotated mockup.

For selected Apple/Android targets, route to the installed Impeccable native references where useful. Use native conventions as a baseline, reconciled with adopted identity and governing requirements. Runtime builds and simulator setup are separate from static design authoring and depend on available tools and authorized scope.

## Games

Ground the visual system in the documented player experience, art direction and game context. Specify HUD hierarchy, readable play-space overlays, menus, pause/settings, inventory or other screens only when the game requires them. Separate diegetic UI, world-space UI, and screen-space UI when relevant. Document readable contrast over variable backgrounds, safe display regions, scaling, information priority and unobstructed play areas.

Resolve input methods explicitly: touch, pointer/keyboard, controller, or other declared inputs. Show selection/focus, back/cancel, input prompts, remapping or alternatives where required, and transitions between play/menu states. Motion, visual/audio/haptic feedback, subtitles, color-independent cues and reduced-motion options follow source scope and accessibility needs. Mock visual/audio/haptic cues describe behavior; they do not prove engine integration.

Use annotated screen images and state storyboards to show the player context when engine rendering is absent. An available declared-engine adapter can inform component ownership, units, scaling and exports. Engine selection does not authorize game scaffolding or gameplay implementation. Mechanics, economy, levels and gameplay code enter the assignment only through an explicit request or governing requirements.

## Multiple targets or unspecified platform

Share primitive/semantic intent, brand, component meaning and consequential state semantics. Override target-specific spacing, navigation, input hints or typography only with rationale. Keep overrides keyed by declared target IDs and validate aliases against the effective shared-plus-override token set.

When platform remains unspecified, produce neutral anatomy/interaction/state specifications and annotated visual examples. Record platform decisions that later implementation must resolve; ask only when missing target information prevents a material design decision.
