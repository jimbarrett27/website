import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  GbAgentCurrent, GbAgentLive, GbAgentNotes, GbAgentScripts,
} from '../models/gb-agent.interface';

/**
 * Reads the live gb_agent run straight from the public GCS bucket the home
 * server's publisher writes to (cross-origin, no credentials). The bucket
 * layout is the contract; see `gb-agent.interface.ts`.
 *
 * The JSON files are uploaded with `Cache-Control: no-cache` and fetched
 * without a cache-buster, so each poll is a conditional request: when nothing
 * has changed the bucket answers 304 and no body is sent. That's what keeps a
 * page polling every few seconds cheap.
 */
@Injectable({ providedIn: 'root' })
export class GbAgentService {
  private http = inject(HttpClient);
  private base = environment.gbAgentBucketBase;

  getCurrent(): Observable<GbAgentCurrent> {
    return this.http.get<GbAgentCurrent>(`${this.base}/current.json`);
  }

  getLive(run: string): Observable<GbAgentLive> {
    return this.http.get<GbAgentLive>(`${this.base}/runs/${run}/live.json`);
  }

  /** Fetched only when `live.json`'s `notes_version` changes. */
  getNotes(run: string): Observable<GbAgentNotes> {
    return this.http.get<GbAgentNotes>(`${this.base}/runs/${run}/notes.json`);
  }

  /** Fetched only when `live.json`'s `scripts_version` changes. */
  getScripts(run: string): Observable<GbAgentScripts> {
    return this.http.get<GbAgentScripts>(`${this.base}/runs/${run}/scripts.json`);
  }

  /** A clip's URL from its bucket-relative key. Clips are immutable. */
  clipUrl(key: string): string {
    return `${this.base}/${key}`;
  }
}
