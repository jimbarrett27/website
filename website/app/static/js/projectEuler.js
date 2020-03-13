window.jimActiveDisplaySolutionFunction = null;

let initialiseRequestButton = function (problemNumber, problemName, problemDescription, requestButton) { // jshint ignore:line
               
    "use strict";
    let displayCode = async function ()
    {
        const source = document.querySelector('.exerciseSource');
        const title = document.querySelector('.exerciseTitle');
        const description = document.querySelector('.exerciseDescription');
        const solution = document.querySelector('.solution');
        const runCodeButton = document.querySelector('.runCode');
        const solutionDiv = document.querySelector('.solutionDiv');

        window.jimActiveProblem = problemNumber;
        if (window.jimActiveDisplaySolutionFunction !== null) {
            runCodeButton.removeEventListener('click', window.jimActiveDisplaySolutionFunction);
        }

        solutionDiv.style.display = "block";

        solution.innerText = "";

        title.innerText = `Problem ${problemNumber} - ${problemName}`;
        description.innerHTML = problemDescription;

        let response = await fetch(`/project_euler_solution_code/${problemNumber}`);
        source.innerText = await response.text();
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightBlock(block); // jshint ignore:line
        });

        let displayAnswer = async function ()
        {
            solution.innerText = "";
            
            solution.innerText = "Calculating";
            
            const xmlRequest = new XMLHttpRequest();
            await xmlRequest.open("GET", `/project_euler_solution/${problemNumber}`, true);
            await xmlRequest.send();

            async function waitForAnswer() {
                return await new Promise(resolve => {
                    let i = 0;
                    const interval = setInterval(() => {
                        // Animation for ellipses
                        solution.innerText = "Calculating" + Array.from({ length: i%4 }).fill('.').join('');
                        if (xmlRequest.readyState === XMLHttpRequest.DONE && xmlRequest.responseText !== '1') {
                            resolve();
                            clearInterval(interval);
                        }
                        i += 1;
                    }, 500);
                });
            }

            await waitForAnswer();

            let responses = xmlRequest.responseText.split('\n');
            solution.innerText = responses[responses.length - 1];

        
        };

        runCodeButton.addEventListener('click', displayAnswer);
        window.jimActiveDisplaySolutionFunction = displayAnswer;
        MathJax.Hub.Queue(["Typeset", MathJax.Hub]); // jshint ignore:line

    };

    requestButton.addEventListener('click', displayCode);

};