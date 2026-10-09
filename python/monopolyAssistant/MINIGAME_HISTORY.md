# Mini-game support history

Dates below are the earliest dated implementation or live-verification evidence
in RULES.md, CODEX_HANDOFF.md and code comments. They are not backdated Git commit
dates. The first tracked source snapshot is `f229c71` (September 13, 2026);
`3cf46e9` synchronized its duplicate script. Later mini-game work remained in the
working tree until the October 9 maintenance snapshot.

| Mini-game type | Earliest documented support | Git evidence and later changes |
| --- | --- | --- |
| Raid / heist target selection | September 6, 2026 | Present in `f229c71`; fresh foreground checks and bounded target handling retained. October 9, 2026: space-themed red reticles distinguished from white background crosses; live COLLECT recovery verified. |
| Match-3 tile reveal | September 6, 2026 | Present in `f229c71`; the original handoff describes automated tile reveal. |
| Jail / bonus-roll screen | September 6, 2026 | Present in `f229c71`; specific purple-roll handling precedes generic popup detection. |
| Color Wheel | September 7, 2026 | Present in `f229c71`; blue SPIN layout documented September 19; title/count verification improved October 6. |
| Pick a Box | September 7, 2026 recognition; September 15 automatic picking | The recognition-only handler is in `f229c71`. RULES.md dates the automatic pick/poll/retry implementation to September 15. |
| Treasure digging | September 23, 2026 | Dated treasure sections document detection, hammer-count checks and blue-star tiles; gold-star/reinforced tiles added that day. |
| Halloween house choices | September 23, 2026 | Dated live recovery; wrapped player title fixed October 2; observed OCR separator fixed October 9. |
| Blocks Boutique | October 4, 2026 | Recipe-one completion and later placements documented in BOUTIQUE_WALKTHROUGH.md; autonomous dragging remains default-off pending further calibration. |
| Mummy Adventures tutorial / Scottie Statue | October 9, 2026 | Live tutorial review and one-token action calibration; bounded five-draw visits with verified spending. Later objects, chests and full completion remain unverified. See MUMMY_ADVENTURES_WALKTHROUGH.md. |
| Spooky Express progress overview | October 9, 2026 | Recognizes the observed First Class/Reach-to-upgrade overview and its grey footer X, then returns to board play. This is an overview recovery handler, not automated upgrades or a general train-event solver. |

Quick Wins and free-gift collection are reward handlers, not separate mini-game
solvers. Railroad Chance (September 23) is a transition handler. Unknown layouts
remain unsupported; an implementation date does not establish universal event
coverage.

## Commit comments

New maintenance commit bodies should name the affected mini-game, the documented
introduction date, the concrete fix, tests and live verification. Keep original
commit dates intact. Historical annotations are Git notes, visible with:

```text
git log --show-notes -- python/monopolyAssistant python/localnet-bin/monopoly-go-assist
```

The October 9 fix accepts only whitespace and the observed vertical separator
between the possessive player name and BOARD. Multiple verified house rings are
still required. It does not repair guessed words, enable Boutique autoplay, or
alter purchase guards.
