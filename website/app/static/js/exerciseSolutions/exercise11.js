import {loadFile} from "../libraryFunctions/loadFile.js"

function exercise11()
{
	const inputData = loadFile('/static/data/projectEuler/exercise11Data.txt').split("\n");
	
	var grid = []
	for (let row of inputData)
	{
		grid.push(row.split(" "))
	}

	let biggest = -1;

	// rows
	for (let i=0; i<grid.length; i++)
	{
		for (let j=0; j<grid[0].length - 4; j++)
		{
			let product = 1;
			for (let k=0; k<4; k++)
			{
				product *= grid[i][j+k]
			}
			if (product > biggest) biggest = product;
		}
	}

	// columns
	for (let i=0; i<grid.length; i++)
	{
		for (let j=0; j<grid[0].length - 4; j++)
		{
			let product = 1;
			for (let k=0; k<4; k++)
			{
				product *= grid[j+k][i]
			}
			if (product > biggest) biggest = product;
		}
	}

	// UL-DR diagonals
	for (let i=0; i<grid.length - 4; i++)
	{
		for (let j=0; j<grid[0].length - 4; j++)
		{
			let product = 1;
			for (let k=0; k<4; k++)
			{
				product *= grid[i+k][j+k]
			}
			if (product > biggest) biggest = product;
		}
	}

	// UR-DL diagonals
	for (let i=4; i<grid.length; i++)
	{
		for (let j=0; j<grid[0].length - 4; j++)
		{
			let product = 1;
			for (let k=0; k<4; k++)
			{
				product *= grid[i-k][j+k]
			}
			if (product > biggest) biggest = product;
		}
	}

	return biggest;

}

export { exercise11 as default }