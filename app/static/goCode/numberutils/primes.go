package numberutils

func PrimesUpTo(max int) (primes []int) {

	var sieve = make([]bool, max)
	for i := range sieve {
		sieve[i] = false
	}

	sieve[0] = true

	primes = append(primes, 1)

	for i := range sieve {
		if sieve[i] == true {
			continue
		}
		sieve[i] = true
		primes = append(primes, i+1)
		for j := i; j < max; j += i + 1 {
			sieve[j] = true
		}
	}

	return
}
