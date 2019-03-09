import {loadFile} from "./loadFile.js";

function expandJavaScript(path)
{
	let js = loadFile(path);

	let lines = js.split('\n')

	let importLines = []
	let otherLines = []
	for (let line of lines)
	{
		if (line.startsWith('import')) importLines.push(line);
		else if (line.startsWith('export')) continue;
		else otherLines.push(line);
	}

	let expanded = []
	for (let importLine of importLines)
	{
		let path = importLine.split('"')[1];
		expanded.push(expandJavaScript('/static/js/libraryFunctions/' + path));
	}

	for (let otherLine of otherLines)
	{
		expanded.push(otherLine)
	}

	return expanded.join('\n')
}

export { expandJavaScript as default }