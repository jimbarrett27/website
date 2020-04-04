package numberutils

import (
	"math"
)

func FindDivisors(num int) (divisors []int) {

	if num == 2 {
		return []int{1, 2}
	}
	if num == 3 {
		return []int{1, 3}
	}

	maxDivisor := int(math.Ceil(math.Sqrt(float64(num))))
	for i := 1; i < maxDivisor; i++ {
		if num%i == 0 {
			divisors = append(divisors, i)
			pairedDivisor := num / i
			if pairedDivisor != maxDivisor {
				divisors = append(divisors, num/i)
			}
		}
	}

	if num%maxDivisor == 0 {
		divisors = append(divisors, maxDivisor)
	}

	return
}
