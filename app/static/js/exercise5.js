function exercise5()
{
	let i=0;
	let done=false;

	outerWhile:
	while (!done)
	{
		i+=20;
		for (let j=2; j<=20; j++)
		{
			if (i % j != 0) continue outerWhile;
		}

		break;
	}

	return i;
}

export { exercise5 as default };