import { Routes } from '@angular/router';

/**
 * Lazy-loaded triage feature routes. Mounted at /triage by the root router.
 * The history view (/triage/history) is added in build step 8.
 */
export const TRIAGE_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/queue/queue.component').then((m) => m.QueueComponent),
  },
];
