import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Decision, Paper } from '../models/paper.model';
import { environment } from '../../../environments/environment';

/**
 * Typed wrapper over the triage backend.
 *
 * The base comes from the environment: in dev it is a relative path forwarded
 * to the local FastAPI server via proxy.conf.json; in production it is the
 * absolute Cloudflare Tunnel host (triage-api.jimbarrett.dev), since the SPA on
 * jimbarrett.dev calls it cross-origin. `withCredentials` lets the browser send
 * the Cloudflare Access cookie on those cross-origin requests.
 */
@Injectable({ providedIn: 'root' })
export class TriageApiService {
  private http = inject(HttpClient);
  private readonly base = environment.triageApiBase;
  private readonly opts = { withCredentials: true };

  /** Pending papers awaiting a triage decision, newest screening first. */
  getQueue(): Observable<Paper[]> {
    return this.http.get<Paper[]>(`${this.base}/queue`, this.opts);
  }

  /** Already-decided papers, newest decision first (history view). */
  getHistory(): Observable<Paper[]> {
    return this.http.get<Paper[]>(`${this.base}/history`, this.opts);
  }

  // Writes send an empty body and pass data via query params so the browser
  // treats them as "simple" cross-origin requests and skips the CORS preflight
  // (Cloudflare's edge rejects the OPTIONS preflight; the Access cookie still
  // rides along on the actual request via withCredentials).

  /** Record a triage decision for a paper. */
  decide(paperId: number, decision: Decision): Observable<Paper> {
    return this.http.post<Paper>(`${this.base}/papers/${paperId}/decide`, null, {
      ...this.opts,
      params: { decision },
    });
  }

  /** Revert the most recent decision (only succeeds within the undo window). */
  undo(paperId: number): Observable<Paper> {
    return this.http.post<Paper>(`${this.base}/papers/${paperId}/undo`, null, this.opts);
  }
}
