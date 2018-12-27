function exercise4()
{
	var biggest = -1;

	for (let i=100; i<1000; i++)
	{
		for(let j=100; j<i; j++)
		{
			let product = i*j;

			let productString = product.toString(10);
			let reversedString = productString.split("").reverse().join("");

			if (productString === reversedString && product > biggest)
			{
				biggest = product;
			}	
		}
	}

	return biggest;
}

export { exercise4 as default };