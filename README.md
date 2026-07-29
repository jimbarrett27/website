# jimbarrett.dev

Personal monorepo — hobby automation and the site that fronts some of it.

- **`website/`** — [jimbarrett.dev](https://jimbarrett.dev), an Angular SPA on Google App Engine.
- **Everything else** — a Python project (`uv`) of Telegram bots and daily jobs:
  paper triage, the news tapestry, content screening, memes, D&D tooling, and assorted others.

Two features deliberately span both: the **paper triage** app (FastAPI backend in
`triage/`, UI at `/triage`) and the **news tapestry** (generator in `tapestry/`, page on
the site). They were previously split across two repos and merged here in July 2026 so
that a change to an API contract and its consumer land in one commit.

See `CLAUDE.md` for layout and `DEVLOG.md` for decisions.
