import { GbAgentActivity } from '../../core/models/gb-agent.interface';

/** One model turn in the log: what it said, what it called, what came back. */
export interface LogTurn {
  key: string;
  text: string | null;
  calls: string[];
  results: LogResult[];
}

export interface LogResult {
  text: string;
  /** good: the screen changed; warn: it barely did; bad: the step failed; info: not a step. */
  tone: 'good' | 'warn' | 'bad' | 'info';
}

function parse(json: string | null | undefined): unknown {
  if (!json) return null;
  try {
    return JSON.parse(json);
  } catch {
    return null;  // trimmed by the publisher, so possibly cut mid-way
  }
}

function value(v: unknown): string {
  const s = typeof v === 'string' ? `"${v}"` : JSON.stringify(v);
  return s.length > 40 ? s.slice(0, 39) + '…' : s;
}

function kwargs(args: unknown): string {
  if (!args || typeof args !== 'object') return '';
  return Object.entries(args).map(([k, v]) => `${k}=${value(v)}`).join(', ');
}

/** `walk(direction="left", steps=2)` from a script name and its JSON args. */
export function scriptCall(script: string | null | undefined, args: string | null | undefined): string {
  if (!script) return 'one-off code';
  return `${script}(${kwargs(parse(args))})`;
}

/** A tool call as the log shows it; run_script shows the script itself. */
export function formatCall(name: string, argsJson: string | null | undefined): string {
  const args = parse(argsJson) as Record<string, unknown> | null;
  if (name === 'run_script' && typeof args?.['name'] === 'string') {
    return `${args['name']}(${kwargs(args['args'])})`;
  }
  if (name === 'update_notes') return 'update_notes(…)';
  if ((name === 'write_script' || name === 'test_script') && typeof args?.['name'] === 'string') {
    return `${name}("${args['name']}", …)`;
  }
  if (name === 'run_code' || name === 'test_code') return `${name}(…)`;
  return `${name}(${kwargs(args)})`;
}

/** "ok · 32 frames · most of the screen changed" from a step's trace text. */
export function summarizeResult(result: string | null | undefined): LogResult {
  const text = result ?? '';
  const first = text.split('\n', 1)[0];
  const frames = text.match(/\((\d+) used\)/)?.[1];
  if (!frames) {
    return { text: first.length > 90 ? first.slice(0, 89) + '…' : first, tone: 'info' };
  }
  const status = first.slice(first.lastIndexOf(': ') + 2).replace(/\s*\[.*$/, '') || 'done';
  const screen = text.match(/screen: (.+?)(?: \(|\n|$)/)?.[1];
  const parts = [status, `${frames} frames`, ...(screen ? [screen] : [])];
  const tone = status !== 'ok' ? 'bad' : /tiny|nothing|didn't/.test(screen ?? '') ? 'warn' : 'good';
  return { text: parts.join(' · '), tone };
}

/** Group activity into model turns, newest first. */
export function toTurns(activity: GbAgentActivity[]): LogTurn[] {
  const turns: LogTurn[] = [];
  for (const a of activity) {
    if (a.kind === 'llm') {
      turns.push({
        key: `${a.time}`,
        text: a.text || a.reasoning || null,
        calls: (a.tool_calls ?? []).map(c => formatCall(c.name, c.args)),
        results: [],
      });
    } else if (a.kind === 'tool') {
      const result = summarizeResult(a.result);
      if (turns.length) turns[turns.length - 1].results.push(result);
      else turns.push({ key: `${a.time}`, text: null, calls: [formatCall(a.tool ?? '?', a.args)], results: [result] });
    } else if (a.kind === 'compaction') {
      turns.push({ key: `${a.time}`, text: null, calls: [], results: [
        { text: 'context full: cleared, keeping only its notes', tone: 'info' }] });
    }
  }
  return turns.reverse();
}

function escape(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/** The agent's markdown-ish notes as safe HTML: paragraphs, **bold** and `code`. */
export function notesHtml(notes: string): string {
  return notes.trim().split(/\n\s*\n/).map(p => '<p>' + escape(p)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>') + '</p>').join('');
}

/** Game time as m:ss (or h:mm:ss) from a frame count. */
export function gameTime(frame: number | undefined, fps = 60): string {
  const s = Math.floor((frame ?? 0) / fps);
  const mmss = `${Math.floor(s / 60) % 60}:${String(s % 60).padStart(2, '0')}`;
  return s >= 3600 ? `${Math.floor(s / 3600)}:${mmss.padStart(5, '0')}` : mmss;
}
