import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PublicationsData } from '../models/publication.interface';

@Injectable({ providedIn: 'root' })
export class PublicationsService {
  private http = inject(HttpClient);

  getPublications(): Observable<PublicationsData> {
    return this.http.get<PublicationsData>('/assets/data/publications.json');
  }
}
