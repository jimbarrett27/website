function loadFile(path)
{
	var fileContents;

	function listener()
	{
		fileContents = this.responseText;
	}
	
	var req = new XMLHttpRequest();
	req.addEventListener("load", listener);
	req.open('GET', path, false);
	req.send();

	return fileContents;
}

export { loadFile }
export { loadFile as default }