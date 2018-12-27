import {primeNumberGenerator} from "./primeNumbers.js";

function exercise10()
{
	let gen = primeNumberGenerator(2000000);

	var sum = 0;
	while (true)
	{
		let prime = gen.next();
		if (prime.done) break;
		sum += prime.value;
	}

	return sum;
}

export { exercise10 as default }