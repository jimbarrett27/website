import {primeNumberGenerator} from '../libraryFunctions/primeNumberGenerator.js';

/**
 * Solution to project euler exercise 3
 */
function exercise3() {
  const gen = primeNumberGenerator(1000000);

  let target = 600851475143;

  while (target > 1) {
    var currentPrime = gen.next().value;

    while (target % currentPrime === 0) {
      target = target / currentPrime;
    }
  }

  return currentPrime;
}

export {exercise3 as default};
