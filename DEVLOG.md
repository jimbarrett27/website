# Devlog

Decisions and milestones for this repo, newest first. One `### entry` per decision or
milestone under a `## YYYY-MM-DD` date header — capture the *why*, not just the *what*.

## 2026-06-08

### Triage UI: single Keep action; depth badge removed

Frontend half of the triage decision/status cleanup (backend spec lives in
`telegram_bot/triage/SPEC-decision-status-cleanup.md`). In real use the `deep` vs
`filed` distinction wasn't pulling its weight, so the two keep-buttons collapse
into one **Keep** action (status `kept`, routes to Zotero + Obsidian); `Dismiss`
unchanged. Both `d` and `f` keyboard shortcuts now trigger Keep so existing muscle
memory still works.

Removed the screener's `suggested_depth` hint badge from the card — it's a model
feature, not a decision the user acts on, and it added visual noise. `TriageStatus`
gains `kept` and `auto_rejected` (plus legacy `deep`/`filed`, still rendered in
History); `Decision` is now `'kept' | 'dismissed'`. Routing badges trigger Zotero
on `kept`/legacy-`deep` and Obsidian on `kept`/legacy-`deep`/`filed`.

`npm run build` + `ng lint` green. Needs a rebuild + App Engine redeploy to go
live, and the triage-backend must be on the matching `kept`/`dismissed` API.
