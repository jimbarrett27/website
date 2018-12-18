const answerField4 = document.querySelector('.exercise4Result');
const requestButton4 = document.querySelector('.requestExercise4');

function exercise4()
{

	var product;
	outerloop:
	for (let i=999; i>99; i--)
	{
		for(let j=999; j>i; j--)
		{
			product = (i*j).toString();

			if (product === product.split("").reverse().join(""))
				console.log(i);
				console.log(j);

				break outerloop;
		}
	}

	answerField4.textContent = product;
}

	
requestButton4.addEventListener('click', exercise4);