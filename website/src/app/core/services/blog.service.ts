import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BlogPost, BlogPostSummary } from '../models/blog-post.interface';

@Injectable({ providedIn: 'root' })
export class BlogService {
  private http = inject(HttpClient);

  getBlogList(): Observable<BlogPostSummary[]> {
    return this.http.get<BlogPostSummary[]>('/assets/blog/index.json');
  }

  getBlogPost(slug: string): Observable<BlogPost> {
    return this.http.get<BlogPost>(`/assets/blog/${slug}.json`);
  }
}
