var answerField2 = document.querySelector('.exercise2Result');
var requestButton2 = document.querySelector('.requestExercise2');

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

	answerField2.textContent = total;
}

requestButton2.addEventListener('click', exercise2);