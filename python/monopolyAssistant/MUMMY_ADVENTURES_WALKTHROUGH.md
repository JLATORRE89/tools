# Mummy Adventures walkthrough - October 9, 2026

## Evidence and mechanics

Observed at 1080x2340 on the connected phone. The initial HOW TO ADVENTURE
page explains team levels, collected event tokens, actions, green progress
markers, objects and level goals. The second page introduces optional treasure
chests, including team rewards. These instructions do not establish an optimal
strategy or later-level mechanics.

Level 1 is WAKE THE MUMMY with 0/6 objects completed. Opening the outlined
Scottie Statue shows CLEAR THE STATUE, 0/3 milestones, 17 progress left, and two
observed target-18 actions costing one and three tokens. One-token calibration
spent 137 -> 136 and reduced progress 17 -> 16. A second draw spent 136 -> 135
without reducing progress. Tutorial says a hand equal to or above the target
earns progress; lower totals advance upgrades instead. A free upgrade reward
appeared, with a COLLECT control. It was manually reviewed/collected during
calibration; the subsequent statue screen retained the same two actions.

## Implemented scope

Training here means screenshot/OCR calibration, recorded control fixtures and
deterministic regression cases; no machine-learning weights were trained.
Two introductory tutorial pages use exact heading and masked CONTINUE text
plus measured green control geometry. The event reward requires MUMMY and
ADVENTURES text and the measured COLLECT control. Live autonomous reward
recognition remains unverified until this screen recurs.

The supported action screen requires exact masked SCOTTIE STATUE, exact
CLEAR THE STATUE, a measured grey footer X, readable token balance, readable
targets and precisely the observed green one-/three-token controls. Numbers
require agreeing color/grayscale OCR; costs use color/white-mask agreement.
No guessed digit substitutions or loose numeric matches.

Only the one-token option is selected. After each tap, require exactly one fewer
token within six fresh polls before any further spending. A mismatch latches a
review pause. Success is never inferred from spending. Cap each visit at five
verified one-token draws, then close the statue and observed overview through
the measured footer X. Zero tokens closes without buying refills. Unreadable
controls pause. In-progress/unknown transitions retain the visit budget and
block generic popup actions until a known screen or confirmed main board.

The handler precedes generic popups/build/rolls in the main and dice-wait loops.
Device changes clear calibration-session state; existing focus and keep mode
remain enforced. The assistant does not automatically enter this event from its
board icon, choose arbitrary objects, optimize a card deck, open optional chests,
use the three-token option, or claim all six objects/levels are solved.

## Recorded fixture

fixtures/mummy-statue-controls.png retains only header, action controls, token
balance and grey close regions. Player names and avatars are excluded. Raw
calibration screenshots remain local, outside Git.

## Live OCR follow-up

A resumed visit spent 134->133->132, then paused because three-times scaled grayscale OCR disagreed on the 132 balance. The pause prevented another draw. Reconciled the actual screenshot; two-times color/grayscale reads agree on captured 132,134,135,136 balances. Numeric reads now use that measured scaling; cost masks retain three-times scaling. No character substitutions or uncertain-draw retries. The revised handler verified 132->131 with a deliberately seeded four-draw counter to exercise the five-draw exit boundary without spending five extra tokens.
