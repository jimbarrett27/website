package solutions

import (
	"../numberutils"
)

func Problem10() (sum int) {

	primes := numberutils.PrimesUpTo(2000000)
	sum = 0
	for i := range primes {
		sum += primes[i]
	}
	return
}
