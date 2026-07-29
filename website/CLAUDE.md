# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in
`website/`. It is scoped to this directory — see the repo-root `CLAUDE.md` for the
Python side and for the triage/tapestry contracts that span both.

All paths and commands below are relative to `website/`.

## What this is

Personal website (jimbarrett.dev) — an Angular 21 single-page app deployed as static files to **Google App Engine**. Standalone-component architecture (no NgModules), all routes lazy-loaded. Most of the site is content-driven (home, publications, blog); the `/triage` route is a self-contained feature app that talks to a separate FastAPI backend.

## Commands

```bash
npm start              # ng serve — dev server on :4200 (proxies /api → triage backend, see below)
npm run build          # ng build — runs the prebuild markdown step first, output to dist/website/browser
npm run watch          # dev build in watch mode
npm run lint           # ng lint (eslint) — CI gate, must be green before deploy
npx ng test            # unit tests (Karma); note: components are scaffolded with skipTests, so coverage is sparse
node build-scripts/process-markdown.js   # regenerate blog JSON without a full build
```

`build` is the production configuration by default (`defaultConfiguration: production` in angular.json), which applies bundle budgets and the environment file replacement. There is no separate lint config — eslint flat config lives in `eslint.config.js` (TS + Angular template rules; `app` selector prefix enforced).

### Node / nvm gotcha
Node is managed via **nvm**, so `npm`/`node`/`ng` are only on PATH inside an nvm-activated shell. If a command fails with "command not found", source nvm first (`. "$NVM_DIR/nvm.sh"`). This also bites systemd-style contexts that don't inherit the nvm PATH. If `node_modules` looks stale relative to `package.json`, run `npm install` before building.

## Content pipeline (blog)

Blog posts are **authored as markdown** in `content/blog/*.md(x)` with gray-matter frontmatter. They are **not** read at runtime. The `prebuild` npm hook runs `build-scripts/process-markdown.js`, which converts each post to `src/assets/blog/<slug>.json` (full HTML via `marked`, GFM on) plus an `index.json` summary sorted newest-first. The app fetches those JSON files at runtime via `core/services/blog.service.ts`.

Implication: **editing a `.md` file does nothing until the prebuild script runs.** `npm run build` runs it automatically; for `ng serve` you must re-run `node build-scripts/process-markdown.js` (or restart) to see content changes.

## Routing & structure

- `src/app/app.routes.ts` — root routes, every entry lazy via `loadComponent`. Pages live under `src/app/pages/<name>/`. Shared chrome (header/footer) is in `src/app/shared/components/`; cross-cutting services in `src/app/core/services/`.
- `src/app/triage/` — the triage feature, mounted at `/triage` via `loadChildren` → `TRIAGE_ROUTES`. It is intentionally self-contained (its own pages/services/models/shortcuts) so it can evolve independently of the marketing site.
- `app.config.ts` wires `provideRouter` + `provideHttpClient` (standalone bootstrap, no AppModule).

## Triage backend integration (the cross-origin bit)

The triage UI calls a **separate** FastAPI service that is not part of this repo — it runs on the same server behind a Cloudflare Tunnel + Cloudflare Access.

- **Dev:** `environment.ts` sets `triageApiBase: '/api/triage'`; `proxy.conf.json` forwards `/api` → `http://127.0.0.1:8077` (the local backend). Same-origin, no auth.
- **Prod:** `angular.json` `fileReplacements` swaps in `environment.prod.ts`, whose `triageApiBase` is the absolute `https://triage-api.jimbarrett.dev/api/triage`. App Engine static hosting can't path-proxy to the tunnel, hence the dedicated cross-origin subdomain.
- Because prod is cross-origin behind Cloudflare Access, triage API calls must send `withCredentials: true` (Access cookie), and writes are kept as CORS-"simple" requests (query params, no JSON `Content-Type`) to avoid a preflight that Cloudflare's edge blocks. Keep new triage API calls defensive about missing fields (optional chaining) — the backend and frontend deploy independently and can briefly skew.

## Deploy

Deployment is GCP **Cloud Build → App Engine** (`app.yaml` serves `dist/website/browser` statically with SPA fallback to `index.html`).
- `infrastructure/deploy.yml` — `npm ci` → `npm run build` → `gcloud app deploy`, triggered on merge to `main`.
- `infrastructure/pull_requests.yml` — `npm ci` → `npm run lint` → `npm run build` on PRs.

So: **push triage frontend changes to a branch, merge to main to trigger the deploy.** A frontend change is only live on jimbarrett.dev after that build completes.
