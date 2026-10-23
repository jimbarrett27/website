/**
 * Types mirroring the live gb_agent contract in the public GCS bucket, written
 * by `gb_agent/publish.py` (the authoritative layout is its module docstring).
 *
 * The publisher and the site deploy separately, so everything a newer
 * publisher might add or an older one might lack is optional: read defensively.
 */

/** `current.json` — which run the page shows. */
export interface GbAgentCurrent {
  run: string;
  /** The publisher's view; also check `GbAgentLive.updated_at` for staleness. */
  live?: boolean;
}

/** One kept step, rendered at game speed. */
export interface GbAgentClip {
  step: number;
  /** Object path relative to the bucket root, e.g. `runs/<run>/clips/step00042.mp4`. */
  key: string;
  frames?: number;
  start_frame?: number;
  agent?: string;
  script?: string | null;
  /** The script's arguments as JSON, trimmed; null for one-off code. */
  args?: string | null;
  /** Unix seconds the step finished. */
  time?: number;
}

export interface GbAgentToolCall {
  name: string;
  /** JSON, trimmed. */
  args?: string | null;
}

/** A trimmed `agents.jsonl` record: a model reply, a tool result, or a compaction. */
export interface GbAgentActivity {
  /** Unix seconds. */
  time?: number;
  agent?: string;
  kind: 'llm' | 'tool' | 'compaction' | string;
  step?: number;
  text?: string | null;
  reasoning?: string | null;
  tool_calls?: GbAgentToolCall[];
  tool?: string;
  args?: string | null;
  result?: string | null;
}

/** `runs/<run>/live.json` — status, newest clips, recent activity. */
export interface GbAgentLive {
  run: string;
  game?: string;
  model?: string;
  goal?: string;
  live?: boolean;
  started_at?: string;
  ended_at?: string | null;
  stop_reason?: string | null;
  frame?: number;
  frame_budget?: number;
  steps?: number;
  kept_steps?: number;
  llm_calls?: number;
  minutes?: number;
  fps?: number;
  /** Oldest first. */
  clips?: GbAgentClip[];
  /** Oldest first. */
  activity?: GbAgentActivity[];
  /** Unix seconds of the last agent record: the model has been working since then. */
  waiting_since?: number | null;
  /** How many times each library script has run in this run. */
  script_uses?: Record<string, number>;
  notes_version?: string;
  scripts_version?: string | null;
  /** ISO time the run last wrote its manifest. */
  updated_at?: string;
}

/** `runs/<run>/notes.json` — the agent's own notes. */
export interface GbAgentNotes {
  version: string;
  notes: string;
}

export interface GbAgentScript {
  name: string;
  version: string;
  signature?: string;
  summary?: string;
  code?: string;
  /** How many commits have touched it. */
  changes?: number;
  /** The agent's reason for the latest change. */
  reason?: string | null;
  changed_at?: string | null;
}

export interface GbAgentSubagent {
  name: string;
  version?: string;
  instructions?: string;
  tools?: string[];
  scripts?: string[];
  model?: string;
}

/** `runs/<run>/scripts.json` — the run's script library and sub-agent specs. */
export interface GbAgentScripts {
  version: string;
  scripts?: GbAgentScript[];
  subagents?: GbAgentSubagent[];
}
