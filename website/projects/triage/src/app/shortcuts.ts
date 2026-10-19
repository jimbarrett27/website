export interface Shortcut {
  keys: string[];
  description: string;
}

/** Single source of truth for the keyboard shortcuts shown in the help overlay. */
export const SHORTCUTS: Shortcut[] = [
  { keys: ['j', '↓'], description: 'Move to next paper' },
  { keys: ['k', '↑'], description: 'Move to previous paper' },
  { keys: ['d', 'f'], description: 'Keep (Zotero + Obsidian)' },
  { keys: ['x'], description: 'Dismiss' },
  { keys: ['u'], description: 'Undo last decision (within 30s)' },
  { keys: ['o'], description: 'Open paper URL in a new tab' },
  { keys: ['?'], description: 'Toggle this help' },
];
