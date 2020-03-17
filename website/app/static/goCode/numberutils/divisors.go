package numberutils

import "math"

func FindDivisors(num int) (divisors []int) {

	maxDivisor := int(math.Sqrt(float64(num)))
	for i := 1; i < maxDivisor; i++ {
		if num%i == 0 {
			divisors = append(divisors, i)
			divisors = append(divisors, num/i)
		}
	}

	if num%maxDivisor == 0 {
		divisors = append(divisors, maxDivisor)
	}

	return
}
