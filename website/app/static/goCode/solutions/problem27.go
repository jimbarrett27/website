package solutions

import (
	"../numberutils"
)

func consecutivePrimeCount(a int, b int, sieve []bool, primes []int) (n int) {
	
	var eq int
	for {
		eq = (n*n) + (a*n) + b
		if eq < 0 {
			return
		}
		if eq < len(sieve) && !sieve[eq]  {
			return
		}
		if !numberutils.IsPrime(primes, eq) {
			return
		}
		n++
	}
}

func Problem27() (solution int) {

	primeSieve := numberutils.SieveUpTo(1000000)
	primes := numberutils.PrimesFromSieve(primeSieve)

	var count int
	var bestA int
	var bestB int
	longestCount := 0
	for a:=-1000; a<=1000; a++ {
		for b:=-1000; b<=1000; b++ {
			count = consecutivePrimeCount(a, b, primeSieve, primes)

			if count > longestCount {
				longestCount = count
				bestA = a
				bestB = b
			}
		}
	}

	solution = bestA * bestB

	return
}