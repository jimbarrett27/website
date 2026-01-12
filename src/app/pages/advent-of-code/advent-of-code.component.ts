import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { AdventOfCodeService } from '../../core/services/advent-of-code.service';
import { AocSolution } from '../../core/models/advent-of-code.interface';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-advent-of-code',
  standalone: true,
  imports: [],
  template: `
    <div class="aoc-page">
      <h1>Advent of Code</h1>
      <p class="intro">
        My solutions to <a href="https://adventofcode.com" target="_blank" rel="noopener">Advent of Code</a> puzzles,
        fetched from <a href="https://github.com/jimbarrett27/AdventOfCode" target="_blank" rel="noopener">GitHub</a>.
      </p>

      <!-- Year Carousel -->
      <div class="year-carousel">
        <button
          class="carousel-btn prev"
          (click)="previousYear()"
          [disabled]="currentYearIndex() === 0"
          aria-label="Previous year"
        >
          &larr;
        </button>
        <div class="year-display">
          <span class="year-label">{{ selectedYear() }}</span>
        </div>
        <button
          class="carousel-btn next"
          (click)="nextYear()"
          [disabled]="currentYearIndex() === allYears.length - 1"
          aria-label="Next year"
        >
          &rarr;
        </button>
      </div>

      <!-- Days Grid -->
      <div class="days-grid">
        @for (day of days; track day) {
          <button
            class="day-btn"
            [class.solved]="isDaySolved(day)"
            [class.unsolved]="!isDaySolved(day)"
            (click)="selectDay(day)"
            [attr.aria-label]="'Day ' + day + (isDaySolved(day) ? ' (solved)' : ' (not solved)')"
          >
            {{ day }}
          </button>
        }
      </div>

      <!-- Solution Modal -->
      @if (showModal()) {
        <div class="modal-overlay" (click)="closeModal()">
          <div class="modal-content" (click)="$event.stopPropagation()">
            <div class="modal-header">
              <h2>{{ selectedYear() }} - Day {{ selectedDay() }}</h2>
              <button class="close-btn" (click)="closeModal()" aria-label="Close">&times;</button>
            </div>
            <div class="modal-body">
              @if (loading()) {
                <div class="loading">Loading solution...</div>
              } @else if (currentSolution()) {
                <pre><code>{{ currentSolution()!.content }}</code></pre>
              } @else {
                <div class="not-solved">
                  <p>I haven't solved this problem yet.</p>
                  <p>Check back later!</p>
                </div>
              }
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .aoc-page {
      max-width: 720px;
      margin: 0 auto;
      padding: 2rem 1rem;
    }

    h1 {
      margin-bottom: 0.5rem;
    }

    .intro {
      color: var(--color-gray);
      margin-bottom: 2rem;
    }

    .intro a {
      color: inherit;
      text-decoration: underline;
    }

    .year-carousel {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 1rem;
      margin-bottom: 2rem;
    }

    .carousel-btn {
      background: var(--color-black);
      color: var(--color-white);
      border: none;
      padding: 0.5rem 1rem;
      font-size: 1.25rem;
      cursor: pointer;
      border-radius: 4px;
      transition: opacity 0.2s;
    }

    .carousel-btn:disabled {
      opacity: 0.3;
      cursor: not-allowed;
    }

    .carousel-btn:not(:disabled):hover {
      opacity: 0.8;
    }

    .year-display {
      min-width: 100px;
      text-align: center;
    }

    .year-label {
      font-size: 2rem;
      font-weight: bold;
    }

    .days-grid {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 0.75rem;
      max-width: 400px;
      margin: 0 auto;
    }

    .day-btn {
      aspect-ratio: 1;
      border: 2px solid var(--color-gray-light);
      border-radius: 8px;
      font-size: 1.25rem;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.2s;
      background: var(--color-white);
      color: var(--color-black);
    }

    .day-btn.solved {
      background: var(--color-black);
      color: var(--color-white);
      border-color: var(--color-black);
    }

    .day-btn.unsolved {
      background: var(--color-gray-lighter);
      color: var(--color-gray);
      border-color: var(--color-gray-light);
    }

    .day-btn:hover {
      transform: scale(1.05);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }

    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.6);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 1rem;
    }

    .modal-content {
      background: var(--color-white);
      border-radius: 8px;
      max-width: 800px;
      width: 100%;
      max-height: 80vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 1.5rem;
      border-bottom: 1px solid var(--color-gray-light);
    }

    .modal-header h2 {
      margin: 0;
      font-size: 1.25rem;
    }

    .close-btn {
      background: none;
      border: none;
      font-size: 1.5rem;
      cursor: pointer;
      padding: 0;
      line-height: 1;
      color: var(--color-gray);
    }

    .close-btn:hover {
      color: var(--color-black);
    }

    .modal-body {
      padding: 1.5rem;
      overflow-y: auto;
      flex: 1;
    }

    .modal-body pre {
      margin: 0;
      background: var(--color-gray-lighter);
      padding: 1rem;
      border-radius: 4px;
      overflow-x: auto;
      font-size: 0.875rem;
      line-height: 1.5;
    }

    .modal-body code {
      font-family: var(--font-family);
    }

    .loading, .not-solved {
      text-align: center;
      padding: 2rem;
      color: var(--color-gray);
    }

    .not-solved p {
      margin: 0.5rem 0;
    }

    @media (max-width: 500px) {
      .days-grid {
        gap: 0.5rem;
      }

      .day-btn {
        font-size: 1rem;
      }

      .year-label {
        font-size: 1.5rem;
      }
    }
  `]
})
export class AdventOfCodeComponent implements OnInit {
  private aocService = inject(AdventOfCodeService);

  allYears = this.aocService.getAllYears();
  days = Array.from({ length: 25 }, (_, i) => i + 1);

  currentYearIndex = signal(0);
  solvedDaysByYear = signal<Map<number, Set<number>>>(new Map());
  showModal = signal(false);
  selectedDay = signal<number | null>(null);
  currentSolution = signal<AocSolution | null>(null);
  loading = signal(false);

  selectedYear = computed(() => this.allYears[this.currentYearIndex()]);

  ngOnInit() {
    this.loadSolvedDays();
  }

  private loadSolvedDays() {
    this.aocService.getYearsWithSolutions().subscribe(yearsWithSolutions => {
      const requests = yearsWithSolutions.map(year =>
        this.aocService.getSolvedDaysForYear(year)
      );

      if (requests.length === 0) return;

      forkJoin(requests).subscribe(results => {
        const solvedMap = new Map<number, Set<number>>();
        yearsWithSolutions.forEach((year, index) => {
          solvedMap.set(year, new Set(results[index]));
        });
        this.solvedDaysByYear.set(solvedMap);
      });
    });
  }

  isDaySolved(day: number): boolean {
    const year = this.selectedYear();
    const solvedDays = this.solvedDaysByYear().get(year);
    return solvedDays?.has(day) ?? false;
  }

  previousYear() {
    if (this.currentYearIndex() > 0) {
      this.currentYearIndex.update(i => i - 1);
    }
  }

  nextYear() {
    if (this.currentYearIndex() < this.allYears.length - 1) {
      this.currentYearIndex.update(i => i + 1);
    }
  }

  selectDay(day: number) {
    this.selectedDay.set(day);
    this.showModal.set(true);

    if (this.isDaySolved(day)) {
      this.loading.set(true);
      this.currentSolution.set(null);
      this.aocService.getSolution(this.selectedYear(), day).subscribe({
        next: solution => {
          this.currentSolution.set(solution);
          this.loading.set(false);
        },
        error: () => {
          this.currentSolution.set(null);
          this.loading.set(false);
        }
      });
    } else {
      this.currentSolution.set(null);
    }
  }

  closeModal() {
    this.showModal.set(false);
    this.selectedDay.set(null);
    this.currentSolution.set(null);
  }
}
