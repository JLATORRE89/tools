# Blocks Boutique walkthrough

Verified on the phone on 2026-10-04 using fresh screenshots and a 15-second
ADB recording (`C:/scratch/monopoly-tutorial.mp4`).

1. Read the recipe's required materials and the event-token balance.
2. Read all 64 cells in the 8x8 grid, distinguishing empty purple cells,
   gold blocks and material tiles with teal frames.
3. Read each drawer shape, including holes and any material-bearing cells.
   Pieces must form one connected shape; never rotate or invent a block.
4. Enumerate placements that fit entirely inside the grid without overlap.
   Prioritize materials collected by completed lines, then completed rows and
   columns, then remaining placement options for the other drawer shapes.
5. Drag from an observed occupied cell. The placement preview is approximately
   400 pixels above the finger on this calibrated 1080x2340 layout. Recheck
   exact Monopoly game foreground before DOWN and MOVE. Always release UP.
6. Capture again. Require the predicted cleared grid and exactly one fewer
   event token before making another placement. An unexpected outcome pauses
   for review; do not repeat the failed placement.
7. Recipe-completion animations use the verified COLLECT reward control.
   The boutique prize cabinet requires GRAND PRIZE and its specific row/column
   instruction plus an exact NEXT label on a dynamically detected green button.
   This transition precedes generic BUILD detection.
8. At zero tokens, leave using guarded Back. Never buy a refill or use a paid
   offer. Unreadable cells, disconnected/unclear pieces and changed geometry
   pause for review.

Live evidence: the tutorial's 3x3 placement collected three tags; two automated
2x3 placements completed recipe 1 and its observed 150-dice reward was collected.
The Next transition reached recipe 2 with 10 tokens. A 2x2 placement then cleared
two columns and collected four materials (10 -> 9 tokens). A T-shaped placement
also matched its predicted result (9 -> 8 tokens). This demonstrates the
observed layout; it does not establish support for every later event mechanic.

Source: `monopoly-go-assist`, kept identical to `../localnet-bin/monopoly-go-assist`
except the Pi runtime's ADB executable path. Real frame fixtures are under
`fixtures/`. Run `python -m unittest test_monopoly_go_assist -q`.


## PAUSED by user: Blocks Boutique review (2026-10-04)
User requested stopping this work and reviewing it later. Pi monopoly-assist.service
was stopped for calibration and must remain stopped until work is resumed.
The new handler is deployed; 124 tests passed on Pi and Windows, but autonomous
execution is NOT fully verified. Recipe 1 completed and its 150-dice reward was
collected. Recipe 2 reached 8 tokens with verified 2x2 and T-shaped placements.
A later top-edge 2x3 placement failed without spending a token; the handler
correctly paused on its unexpected outcome. Manual held-touch calibration also
failed without spending. Latest screenshot still shows recipe 2 and 8 tokens.

Review next: resolve drag-preview alignment, including grab point, piece scaling
and vertical offset near the top edge. Do not blindly retry or change the 400px
offset globally: earlier placements worked, while the latest held previews were
red and overlapped existing cells. Consider recording the complete drag and
verifying the legal preview BEFORE releasing a piece. Retain exact foreground,
touch-release, predicted-outcome and no-purchase guards.

Evidence: C:/scratch/monopoly-tutorial.mp4 (15 seconds),
C:/scratch/boutique-held-fail.png, C:/scratch/boutique-held-corrected.png,
C:/scratch/boutique-corrected.png. Source guide: BOUTIQUE_WALKTHROUGH.md.
Runtime SHA256: 70a3e34c92154714d7394ece92933eb5c9a3c4ff1f67cd9bbf030371e39ca8bd.
Rollback: ~/.local/share/monopoly-assist/backups/20261005T000905Z.
Do not resume automatically or claim the mini-game is finished.

## 2026-10-04 Normal assistant resumed
User explicitly requested that the assistant remain usable and restart. Installed a default-off MONOPOLY_BOUTIQUE_AUTOPLAY gate: unfinished block placement requires explicit opt-in (value 1); a recognized Boutique board pauses for review. Existing normal board play, rewards and purchase guards remain active. 125 tests passed on Windows and Pi. Runtime SHA256 d9b66db63fd2fe4aea0d2cfe97320a1da572f6fb719adee97fd0124ba6988d15. Backup ~/.local/share/monopoly-assist/backups/20261005T002639Z. User service active PID 162661; live main board showed 159 dice and multiplier verification resumed. Earlier request to leave the whole service stopped is superseded; mini-game development remains deferred.
