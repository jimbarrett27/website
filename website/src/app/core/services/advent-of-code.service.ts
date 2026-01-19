import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map, of, catchError } from 'rxjs';
import { GitHubContent, AocSolution } from '../models/advent-of-code.interface';

@Injectable({ providedIn: 'root' })
export class AdventOfCodeService {
  private http = inject(HttpClient);
  private readonly REPO_API_BASE = 'https://api.github.com/repos/jimbarrett27/AdventOfCode/contents';
  private readonly RAW_BASE = 'https://raw.githubusercontent.com/jimbarrett27/AdventOfCode/main';

  /**
   * Get list of years that have solutions in the repo
   */
  getYearsWithSolutions(): Observable<number[]> {
    return this.http.get<GitHubContent[]>(this.REPO_API_BASE).pipe(
      map(contents =>
        contents
          .filter(item => item.type === 'dir' && /^\d{4}$/.test(item.name))
          .map(item => parseInt(item.name, 10))
          .sort((a, b) => b - a)
      ),
      catchError(() => of([]))
    );
  }

  /**
   * Get list of solved days for a specific year
   */
  getSolvedDaysForYear(year: number): Observable<number[]> {
    return this.http.get<GitHubContent[]>(`${this.REPO_API_BASE}/${year}`).pipe(
      map(contents =>
        contents
          .filter(item => item.type === 'file' && /^ex_\d+\.py$/.test(item.name))
          .map(item => {
            const match = item.name.match(/^ex_(\d+)\.py$/);
            return match ? parseInt(match[1], 10) : 0;
          })
          .filter(day => day >= 1 && day <= 25)
          .sort((a, b) => a - b)
      ),
      catchError(() => of([]))
    );
  }

  /**
   * Get the solution content for a specific day
   */
  getSolution(year: number, day: number): Observable<AocSolution> {
    const url = `${this.RAW_BASE}/${year}/ex_${day}.py`;
    return this.http.get(url, { responseType: 'text' }).pipe(
      map(content => ({
        year,
        day,
        content
      }))
    );
  }

  /**
   * Get all years from 2015 to current year
   * Excludes current year if before December 1st
   */
  getAllYears(): number[] {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth(); // 0-indexed (0 = January, 11 = December)

    // Start from current year, but exclude it if we're before December
    const startYear = currentMonth < 11 ? currentYear - 1 : currentYear;

    const years: number[] = [];
    for (let year = startYear; year >= 2015; year--) {
      years.push(year);
    }
    return years;
  }
}
