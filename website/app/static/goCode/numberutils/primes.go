package numberutils

import "math"

func SieveUpTo(max int) (sieve []bool) {

	sieve = make([]bool, max)
	for i := range sieve {
		sieve[i] = false
	}

	sieve[0] = true

	for i := range sieve {
		if sieve[i] == true {
			continue
		}
		for j := i + i + 1; j < max; j += i + 1 {
			sieve[j] = true
		}
	}

	return
}

func PrimesUpTo(max int) (primes []int) {

	sieve := SieveUpTo(max)

	for i := range sieve {
		if !sieve[i] {
			primes = append(primes, i+1)
		}
	}

	return

}

func IsPrime(primes []int, number int) bool {
	maxTrial := int(math.Sqrt(float64(number)))

	if number%2 == 0 {
		return false
	}

	for i := range primes[1:] {
		if number%primes[i] == 0 {
			return false
		}
		if i > maxTrial {
			break
		}
	}

	return true
}
