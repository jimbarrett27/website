import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { TapestryIndex, TapestryPanel } from '../models/tapestry.interface';

/**
 * Reads the news-tapestry panels straight from the public GCS bucket the
 * telegram_bot job writes to (cross-origin, no credentials). The bucket layout
 * is the contract; see `tapestry.interface.ts`.
 */
@Injectable({ providedIn: 'root' })
export class TapestryService {
  private http = inject(HttpClient);
  private base = environment.tapestryBucketBase;

  /** The manifest: geometry + the list of available panel dates.
   *
   *  Cache-busted: the bucket serves objects with `Cache-Control: max-age=3600`,
   *  but the manifest is rewritten daily (a new date is appended), so a cached
   *  copy would hide new panels for up to an hour. A fresh URL each load also
   *  sidesteps stale edge copies that predate the bucket's CORS config. */
  getIndex(): Observable<TapestryIndex> {
    return this.http.get<TapestryIndex>(`${this.base}/index.json?t=${Date.now()}`);
  }

  /** One day's panel (stories + SVG), keyed by date (YYYY-MM-DD). Panels are
   *  immutable once written, so these stay cacheable (no cache-buster). */
  getPanel(date: string): Observable<TapestryPanel> {
    return this.http.get<TapestryPanel>(`${this.base}/panels/${date}.json`);
  }
}
