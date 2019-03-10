import {loadFile} from "../libraryFunctions/loadFile.js"

function exercise13()
{
	var bigIntegers = loadFile('/static/data/projectEuler/exercise13Data.txt').split("\n");

	var total = BigInt(0);
	for (let integer of bigIntegers)
	{
		total = total + BigInt(integer);
	}
	
	return total.toString().slice(0,10);
}

export { exercise13 as default }