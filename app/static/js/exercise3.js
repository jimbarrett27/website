const answerField3 = document.querySelector('.exercise3Result');
const requestButton3 = document.querySelector('.requestExercise3');

import {primeNumberGenerator} from "./primeNumbers.js";

function exercise3() {
	
	let gen = primeNumberGenerator(1000000);

	let target = 600851475143;

	while (target > 1)
	{
		var currentPrime = gen.next().value;

		while (target % currentPrime === 0)
		{
			target = target / currentPrime;
		}

	}

	answerField3.textContent = currentPrime;
}

requestButton3.addEventListener('click', exercise3);