export type SuggestedDepth = 'deep' | 'skim' | 'file';

export type TriageStatus = 'pending' | 'deep' | 'filed' | 'dismissed';

/** Mirrors the backend `PaperOut` schema (GET /api/triage/queue). */
export interface Paper {
  id: number;
  title: string;
  authors: string[];
  source_type: string;
  url: string;
  abstract: string | null;
  /** ISO 8601 UTC timestamp of when the pipeline discovered the paper. */
  discovered_at: string;
  llm_interest_score: number | null;
  /** The "why this surfaced" reason shown on the card. */
  llm_reasoning: string | null;
  llm_tags: string[];
  suggested_depth: SuggestedDepth | null;
  status: TriageStatus;
  /** ISO 8601 UTC timestamp of the triage decision; null while pending. */
  decided_at: string | null;
}

/** The decisions a paper can be routed to (the `pending` status is the absence of a decision). */
export type Decision = Exclude<TriageStatus, 'pending'>;
