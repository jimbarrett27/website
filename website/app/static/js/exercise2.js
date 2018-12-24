function exercise2() {
	
	let prev = 0;
	let current = 1;

	let total = 0;
	while (current < 4000000)
	{
		let nextVal = current + prev;
		
		if (nextVal % 2 == 0)
		{
			total += nextVal;					
		}
		
		prev = current;
		current = nextVal;

	}

	return total;
}

export { exercise2 as default }