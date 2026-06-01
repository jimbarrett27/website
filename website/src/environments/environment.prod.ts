/**
 * Production environment.
 *
 * The SPA is served from https://jimbarrett.dev (App Engine) but the triage
 * backend lives on a separate Cloudflare Tunnel host, so the API base must be
 * the absolute cross-origin URL. App Engine static hosting can't path-proxy to
 * the tunnel, which is why a dedicated subdomain is used.
 */
export const environment = {
  production: true,
  triageApiBase: 'https://triage-api.jimbarrett.dev/api/triage',
};
