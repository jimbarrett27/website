export interface AocSolution {
  year: number;
  day: number;
  content: string;
}

export interface AocYearData {
  year: number;
  solvedDays: Set<number>;
}

export interface GitHubContent {
  name: string;
  path: string;
  type: 'file' | 'dir';
  download_url: string | null;
}
