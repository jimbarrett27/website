import {loadFile} from './loadFile.js';

function expandJavaScript(path) {
  const js = loadFile(path);

  const lines = js.split('\n');

  const importLines = [];
  const otherLines = [];
  for (const line of lines) {
    if (line.startsWith('import')) importLines.push(line);
    else if (line.startsWith('export')) continue;
    else otherLines.push(line);
  }

  const expanded = [];
  for (const importLine of importLines) {
    const path = importLine.split('"')[1];
    expanded.push(expandJavaScript('/static/js/libraryFunctions/' + path));
  }

  for (const otherLine of otherLines) {
    expanded.push(otherLine);
  }

  return expanded.join('\n');
}

export {expandJavaScript as default};
