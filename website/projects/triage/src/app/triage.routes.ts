import { Routes } from '@angular/router';

/**
 * Triage app routes. The app is served on its own host, so the queue sits at
 * the root.
 */
export const TRIAGE_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/queue/queue.component').then((m) => m.QueueComponent),
  },
];
