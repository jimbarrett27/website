import { Component, computed, input, output, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Decision, Paper } from '../../models/paper.model';

/**
 * Presentational card for a single paper in the triage queue.
 *
 * Owns only its own local UI state (abstract expand/collapse). Focus and
 * keyboard handling live in the queue page, which drives the `focused` input.
 */
@Component({
  selector: 'app-paper-card',
  standalone: true,
  imports: [DatePipe],
  template: `
    <article class="card" [class.focused]="focused()">
      <header class="card-head">
        <h2 class="title">{{ paper().title }}</h2>
        @if (paper().suggested_depth; as depth) {
          <span class="badge" [class]="'badge-' + depth" [title]="depthHint(depth)">
            {{ depth }}
          </span>
        }
      </header>

      <p class="meta">
        <span class="authors">{{ authorsLabel() }}</span>
        <span class="sep">·</span>
        <span class="source">{{ paper().source_type }}</span>
        <span class="sep">·</span>
        <time>{{ paper().discovered_at | date: 'mediumDate' }}</time>
      </p>

      @if (paper().abstract) {
        <p
          class="abstract"
          [class.clamped]="!expanded()"
          (click)="toggleAbstract()"
          [title]="expanded() ? 'Click to collapse' : 'Click to expand'"
        >
          {{ paper().abstract }}
        </p>
      }

      @if (paper().llm_reasoning) {
        <p class="reason"><strong>Why this surfaced:</strong> {{ paper().llm_reasoning }}</p>
      }

      @if (paper().llm_tags.length) {
        <p class="tags">
          @for (tag of paper().llm_tags; track tag) {
            <span class="tag">{{ tag }}</span>
          }
        </p>
      }

      <div class="actions">
        <button
          class="act act-deep"
          (click)="$event.stopPropagation(); decide.emit('deep')"
          title="Mark for deep reading (d)"
        >
          Deep
        </button>
        <button
          class="act"
          (click)="$event.stopPropagation(); decide.emit('filed')"
          title="File for later (f)"
        >
          File
        </button>
        <button
          class="act act-dismiss"
          (click)="$event.stopPropagation(); decide.emit('dismissed')"
          title="Dismiss (x)"
        >
          Dismiss
        </button>
        <button
          class="act act-open"
          (click)="$event.stopPropagation(); open.emit()"
          title="Open paper URL in a new tab (o)"
        >
          Open ↗
        </button>
      </div>
    </article>
  `,
  styles: [
    `
      .card {
        border: 1px solid var(--color-gray-light);
        border-radius: 8px;
        padding: 1rem 1.25rem;
        background: var(--color-white);
        transition:
          border-color 0.15s,
          box-shadow 0.15s;
        scroll-margin: 5rem;
      }

      .card.focused {
        border-color: var(--color-black);
        box-shadow: 0 0 0 2px var(--color-black);
        background: var(--color-gray-lighter);
      }

      .card-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.75rem;
      }

      .title {
        font-size: 1.15rem;
        line-height: 1.35;
        margin: 0;
      }

      .badge {
        flex-shrink: 0;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        padding: 0.15rem 0.5rem;
        border-radius: 999px;
        border: 1px solid transparent;
      }
      .badge-deep {
        background: var(--color-black);
        color: var(--color-white);
      }
      .badge-skim {
        background: var(--color-gray);
        color: var(--color-white);
      }
      .badge-file {
        background: var(--color-gray-lighter);
        color: var(--color-gray);
        border-color: var(--color-gray-light);
      }

      .meta {
        color: var(--color-gray);
        font-size: 0.85rem;
        margin: 0.4rem 0 0.6rem;
      }
      .sep {
        margin: 0 0.4rem;
      }

      .abstract {
        margin: 0 0 0.6rem;
        cursor: pointer;
      }
      .abstract.clamped {
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .reason {
        margin: 0 0 0.6rem;
        font-size: 0.95rem;
      }

      .tags {
        margin: 0;
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
      }
      .tag {
        font-size: 0.75rem;
        color: var(--color-gray);
        background: var(--color-gray-lighter);
        border: 1px solid var(--color-gray-light);
        border-radius: 4px;
        padding: 0.05rem 0.4rem;
      }

      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.9rem;
        padding-top: 0.9rem;
        border-top: 1px solid var(--color-gray-light);
      }
      .act {
        font-family: var(--font-family);
        font-size: 0.85rem;
        cursor: pointer;
        padding: 0.3rem 0.75rem;
        border-radius: 6px;
        border: 1px solid var(--color-gray-light);
        background: var(--color-white);
        color: var(--color-black);
        transition:
          background 0.12s,
          border-color 0.12s;
      }
      .act:hover {
        background: var(--color-gray-lighter);
      }
      .act-deep {
        background: var(--color-black);
        color: var(--color-white);
        border-color: var(--color-black);
      }
      .act-deep:hover {
        opacity: 0.85;
        background: var(--color-black);
      }
      .act-dismiss {
        color: var(--color-gray);
      }
      .act-open {
        margin-left: auto;
      }
    `,
  ],
})
export class PaperCardComponent {
  paper = input.required<Paper>();
  focused = input<boolean>(false);

  decide = output<Decision>();
  open = output<void>();

  expanded = signal(false);

  authorsLabel = computed(() => {
    const authors = this.paper().authors;
    if (authors.length === 0) return 'Unknown authors';
    if (authors.length <= 3) return authors.join(', ');
    return `${authors.slice(0, 3).join(', ')} et al.`;
  });

  toggleAbstract(): void {
    this.expanded.update((v) => !v);
  }

  depthHint(depth: string): string {
    switch (depth) {
      case 'deep':
        return 'Worth reading in full';
      case 'skim':
        return 'Worth a quick read of key sections';
      case 'file':
        return 'File the reference; not worth reading now';
      default:
        return '';
    }
  }
}
