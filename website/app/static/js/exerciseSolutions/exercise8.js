import {loadFile} from "../libraryFunctions/loadFile.js"

function exercise8()
{
	var longNumber = loadFile('/static/data/projectEuler/exercise8Data.txt').split("\n").join("");

	var array = longNumber.split("");
	var biggest = -1;
	
	for (let i=0; i<array.length-13; i++)
	{
		let product = 1;
		for (let j=i; j<i+13; j++)
		{
			product *= array[j];
		}

		if (product > biggest) biggest = product;
	}

	return biggest;
}

export { exercise8 as default }