/**
 * Types mirroring the news-tapestry contract in the public GCS bucket
 * (written by the telegram_bot `tapestry` job). See that repo's
 * `tapestry/storage.py` for the authoritative layout.
 */

/** One of the (three) news stories a panel illustrates. */
export interface TapestryStory {
  title: string;
  summary: string;
  link: string;
}

/** Panel geometry shared by every day; drives the client-side stitching. */
export interface TapestryGeometry {
  panel_width: number;
  panel_height: number;
  /** Vertical px consecutive panels overlap by (today drawn over yesterday). */
  overlap: number;
}

/** `tapestry/index.json` — the manifest of available panels. */
export interface TapestryIndex {
  geometry: TapestryGeometry;
  /** Panel dates (YYYY-MM-DD), oldest first — the order the tapestry grew in. */
  dates: string[];
  updated_at?: string;
}

/** `tapestry/panels/<date>.json` — one day's panel. */
export interface TapestryPanel {
  date: string;
  generated_at: string;
  /** OpenRouter id of the model that drew this panel (varies day to day). */
  model: string;
  /** The model's stated plan/reasoning before drawing. Absent on older panels
   *  written before plans were recorded. */
  plan?: string;
  prompt_template: string;
  stories: TapestryStory[];
  svg: string;
}
