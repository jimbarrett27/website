import {
  ChangeDetectionStrategy, Component, DestroyRef, computed, inject, signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { EMPTY, catchError, exhaustMap, fromEvent, map, merge, of, switchMap, timer } from 'rxjs';
import { GbAgentService } from '../../core/services/gb-agent.service';
import {
  GbAgentClip, GbAgentLive, GbAgentNotes, GbAgentScripts,
} from '../../core/models/gb-agent.interface';

const LIVE_POLL_MS = 4_000;
const IDLE_POLL_MS = 60_000;
/** A run whose manifest hasn't been written for this long is shown as offline,
 *  even if the publisher last said it was live (it may have stopped). */
const STALE_MS = 10 * 60_000;
/** If the queue gets further behind than this, skip to the newest clip. */
const MAX_BEHIND_S = 60;

/**
 * The gb_agent bot playing Pokémon, as it happens. Polls the publisher's files
 * in the bucket and plays each kept step's clip back to back at game speed.
 *
 * Bare on purpose: this proves the plumbing. The look is still to be designed.
 */
@Component({
  selector: 'app-gb-agent',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="gb-agent">
      <h1>gb_agent</h1>
      @if (error()) {
        <p>Couldn't reach the bot right now.</p>
      } @else if (!live()) {
        <p>Loading&hellip;</p>
      } @else {
        <p class="status">
          <strong>{{ isLive() ? 'LIVE' : 'offline' }}</strong>
          · {{ live()?.model }} · step {{ live()?.steps }} · frame {{ live()?.frame }}
          @if (!isLive() && live()?.stop_reason) { · ended: {{ live()?.stop_reason }} }
        </p>

        <div class="screen">
          <video #video playsinline [muted]="true"
                 [attr.src]="playing() ? clipUrl(playing()!) : null"
                 (loadeddata)="play(video)" (ended)="next()"></video>
          @if (thinkingFor() !== null) {
            <p class="thinking">thinking&hellip; {{ thinkingFor() }}</p>
          }
          @if (playing(); as clip) {
            <p class="caption">step {{ clip.step }} · {{ clip.script ?? 'one-off code' }}
              · {{ queue().length }} queued</p>
          }
        </div>

        <h2>Activity</h2>
        <ol class="activity" reversed>
          @for (a of activityNewestFirst(); track $index) {
            <li>
              <small>{{ a.kind }} · {{ a.agent }} · step {{ a.step }}</small>
              @if (a.text) { <p>{{ a.text }}</p> }
              @if (a.reasoning) { <p><em>{{ a.reasoning }}</em></p> }
              @for (c of a.tool_calls ?? []; track $index) { <code>{{ c.name }}({{ c.args }})</code> }
              @if (a.kind === 'tool') { <pre>{{ a.tool }} → {{ a.result }}</pre> }
            </li>
          }
        </ol>

        <h2>Notes</h2>
        <pre>{{ notes()?.notes || '(none yet)' }}</pre>

        <h2>Scripts</h2>
        @for (s of scripts()?.scripts ?? []; track s.name) {
          <details>
            <summary><code>{{ s.signature ?? s.name }}</code> @ {{ s.version }} — {{ s.summary }}</summary>
            @if (s.reason) { <p>Last change: {{ s.reason }}</p> }
            <pre>{{ s.code }}</pre>
          </details>
        }
      }
    </div>
  `,
  styles: [`
    .gb-agent { max-width: var(--max-width-wide); margin: 0 auto; padding: 2rem 1rem; }
    .screen { position: relative; width: 320px; max-width: 100%; }
    video { width: 100%; aspect-ratio: 10 / 9; image-rendering: pixelated; background: #000; display: block; }
    .thinking, .caption { font-size: 0.85rem; color: var(--color-gray); margin: 0.25rem 0; }
    .activity li { margin-bottom: 0.75rem; }
    pre { white-space: pre-wrap; }
  `],
})
export class GbAgentComponent {
  private api = inject(GbAgentService);
  private destroyRef = inject(DestroyRef);

  readonly live = signal<GbAgentLive | null>(null);
  readonly notes = signal<GbAgentNotes | null>(null);
  readonly scripts = signal<GbAgentScripts | null>(null);
  readonly error = signal(false);
  readonly playing = signal<GbAgentClip | null>(null);
  readonly queue = signal<GbAgentClip[]>([]);
  /** The last clip has finished and its final frame is held: the model is working. */
  readonly holding = signal(false);
  private readonly now = signal(Date.now());

  /** The newest step already played or queued; clips after it get queued. */
  private lastQueued = -1;
  private run: string | null = null;

  readonly isLive = computed(() => {
    const live = this.live();
    const updated = live?.updated_at ? Date.parse(live.updated_at) : NaN;
    return !!live?.live && this.now() - updated < STALE_MS;
  });

  readonly activityNewestFirst = computed(() => [...(this.live()?.activity ?? [])].reverse());

  /** "m:ss" the model has been working, while live and nothing is playing. */
  readonly thinkingFor = computed(() => {
    const since = this.live()?.waiting_since;
    if (!this.isLive() || (this.playing() && !this.holding()) || !since) return null;
    const s = Math.max(0, Math.floor(this.now() / 1000 - since));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  });

  constructor() {
    timer(0, 1000).pipe(takeUntilDestroyed()).subscribe(() => this.now.set(Date.now()));

    const visible = merge(of(null), fromEvent(document, 'visibilitychange')).pipe(
      map(() => document.visibilityState === 'visible'));
    visible.pipe(
      switchMap(isVisible => isVisible
        ? timer(0, LIVE_POLL_MS).pipe(
            // Idle runs only need checking now and then.
            exhaustMap((i) => (this.isLive() || i % (IDLE_POLL_MS / LIVE_POLL_MS) === 0)
              ? this.poll() : EMPTY))
        : EMPTY),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe();
  }

  clipUrl(clip: GbAgentClip): string {
    return this.api.clipUrl(clip.key);
  }

  /** Browsers only autoplay muted video, and Angular doesn't set the `muted`
   *  property from the attribute, so start each clip by hand. */
  play(video: HTMLVideoElement): void {
    video.muted = true;
    video.play().catch(() => undefined);
  }

  /** Play the next queued clip, or hold the last frame if there isn't one. */
  next(): void {
    const [head, ...rest] = this.queue();
    if (!head) {  // keep `playing` so its last frame stays on screen
      this.holding.set(true);
      return;
    }
    this.holding.set(false);
    this.queue.set(rest);
    this.playing.set(head);
  }

  private poll() {
    return this.api.getCurrent().pipe(
      switchMap(current => {
        if (current.run !== this.run) this.reset(current.run);
        return this.api.getLive(current.run);
      }),
      map(live => this.apply(live)),
      catchError(() => { this.error.set(!this.live()); return EMPTY; }),
    );
  }

  private reset(run: string): void {
    this.run = run;
    this.lastQueued = -1;
    this.queue.set([]);
    this.playing.set(null);
    this.holding.set(false);
    this.notes.set(null);
    this.scripts.set(null);
  }

  private apply(live: GbAgentLive): void {
    const prev = this.live();
    this.live.set(live);
    this.error.set(false);
    const run = live.run;
    if (live.notes_version && live.notes_version !== prev?.notes_version) {
      this.api.getNotes(run).subscribe({ next: n => this.notes.set(n), error: () => undefined });
    }
    if (live.scripts_version && live.scripts_version !== prev?.scripts_version) {
      this.api.getScripts(run).subscribe({ next: s => this.scripts.set(s), error: () => undefined });
    }
    this.enqueue(live.clips ?? [], live.fps ?? 60);
  }

  private enqueue(clips: GbAgentClip[], fps: number): void {
    if (!clips.length) return;
    // A newcomer starts at the newest clip rather than inheriting a backlog.
    const fresh = this.lastQueued < 0 ? clips.slice(-1) : clips.filter(c => c.step > this.lastQueued);
    if (!fresh.length) return;
    this.lastQueued = fresh[fresh.length - 1].step;
    let queue = [...this.queue(), ...fresh];
    const behind = queue.reduce((s, c) => s + (c.frames ?? 0), 0) / fps;
    if (behind > MAX_BEHIND_S) queue = queue.slice(-1);
    this.queue.set(queue);
    if (!this.playing() || this.holding()) this.next();
  }
}
