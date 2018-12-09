const answerField3 = document.querySelector('.exercise3Result');
const requestButton3 = document.querySelector('.requestExercise3');

function* primeNumberGenerator(arraySize)
{
	let sieve = [];
	sieve.length = arraySize;
	sieve.fill(true);

	for (let i=2; i<arraySize; i++)
	{
		if (sieve[i])
		{
			yield i;

			let j = i;
			while (j<arraySize)
			{
				j += i;
				sieve[j] = false
			}
		}
	}
}

function exercise3() {
	
	let gen = primeNumberGenerator(1000000);

	let target = 600851475143;

	while (target > 1)
	{

		console.log(target)
		currentPrime = gen.next().value;

		while (target % currentPrime === 0)
		{
			target = target / currentPrime;
		}

	}

	answerField3.textContent = currentPrime;
}

requestButton3.addEventListener('click', exercise3);