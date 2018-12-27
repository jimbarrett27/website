import {primeNumberGenerator} from "./primeNumbers.js";

function exercise7()
{
	let gen = primeNumberGenerator(1000000);

	let prime;
	
	for (let i=0; i<10001; i++) prime = gen.next().value;

	return prime;
}

export { exercise7 as default }