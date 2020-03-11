package solutions

import (
	"../numberutils"
)

func Problem3() (largestFactor int) {

	var targetNumber int = 600851475143

	var primes = numberutils.PrimesUpTo(1000000)

	for i := len(primes) - 1; i >= 0; i-- {
		if targetNumber%primes[i] == 0 {
			largestFactor = primes[i]
			break
		}
	}

	return
}
