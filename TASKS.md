# Tasks

## 2026-10-09 Monopoly repository branch correction

Started: user clarified Monopoly updates belong in the tools repository, not its Timezones branch. Verified the remote is JLATORRE89/tools and default branch is master. Fast-forwarded existing local master to the existing remote tip; imported only Monopoly source, mirror, tests, fixtures, maintenance skill and related docs from8d9169c. Preserved the historical branch and unrelated repository content.

Preparation completed: documentation identifies tools/master as canonical; dated mini-game introductions and source commit references are retained. Normalized legacy Markdown encoding so the Pi installer can read RULES.md as UTF-8. Application script bytes remain identical to the deployed/tested source. Regression verification and scoped commit/publication follow. No runtime changes required.
