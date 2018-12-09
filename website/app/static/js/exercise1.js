const answerField1 = document.querySelector('.exercise1Result');
const requestButton1 = document.querySelector('.requestExercise1');

function exercise1() {
	
	let total = 0;
	for (let i=0; i<1000; i++)
	{
		if ((i % 3) * (i % 5) === 0) total += i;
	}

	answerField1.textContent = total;
}

requestButton1.addEventListener('click', exercise1);
