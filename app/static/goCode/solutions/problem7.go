package solutions

import (
	"../numberutils"
)

func Problem7() int {
	primes := numberutils.PrimesUpTo(1000000)
	return primes[10000]
}
