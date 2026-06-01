/**
 * Development environment.
 *
 * The triage API base is relative so `ng serve` forwards it to the local
 * FastAPI backend via proxy.conf.json. Replaced at build time for production
 * (see environment.prod.ts + angular.json fileReplacements).
 */
export const environment = {
  production: false,
  triageApiBase: '/api/triage',
};
