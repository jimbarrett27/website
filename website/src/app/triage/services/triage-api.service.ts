import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Decision, Paper } from '../models/paper.model';

/**
 * Typed wrapper over the /api/triage backend.
 *
 * The base path is relative: in dev it is forwarded to the local FastAPI
 * server via proxy.conf.json; in production the edge routes /api/triage/* to
 * the backend behind the Cloudflare Tunnel.
 */
@Injectable({ providedIn: 'root' })
export class TriageApiService {
  private http = inject(HttpClient);
  private readonly base = '/api/triage';

  /** Pending papers awaiting a triage decision, newest screening first. */
  getQueue(): Observable<Paper[]> {
    return this.http.get<Paper[]>(`${this.base}/queue`);
  }

  /** Record a triage decision for a paper. */
  decide(paperId: number, decision: Decision): Observable<Paper> {
    return this.http.post<Paper>(`${this.base}/papers/${paperId}/decide`, { decision });
  }

  /** Revert the most recent decision (only succeeds within the undo window). */
  undo(paperId: number): Observable<Paper> {
    return this.http.post<Paper>(`${this.base}/papers/${paperId}/undo`, {});
  }
}
