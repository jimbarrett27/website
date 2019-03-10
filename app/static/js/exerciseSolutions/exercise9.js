function exercise9()
{
	outerloop:
	for (let a=1; a<400; a++)
	{
		for (let b=1; b<a; b++)
		{
			let c = 1000 - b - a;

			if (a*a + b*b === c*c)
			{
				var answer = a*b*c;
				break outerloop;
			}
		}
	}

	return answer;
}

export { exercise9 as default }