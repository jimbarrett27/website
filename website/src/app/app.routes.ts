import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/home/home.component').then(m => m.HomeComponent)
  },
  {
    path: 'publications',
    loadComponent: () => import('./pages/publications/publications.component').then(m => m.PublicationsComponent)
  },
  {
    path: 'blog',
    loadComponent: () => import('./pages/blog-list/blog-list.component').then(m => m.BlogListComponent)
  },
  {
    path: 'blog/:slug',
    loadComponent: () => import('./pages/blog-post/blog-post.component').then(m => m.BlogPostComponent)
  },
  {
    path: 'advent-of-code',
    loadComponent: () => import('./pages/advent-of-code/advent-of-code.component').then(m => m.AdventOfCodeComponent)
  },
  {
    path: '**',
    redirectTo: ''
  }
];
