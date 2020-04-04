package solutions

import (
	"../numberutils"
)

func findAbundantNumbers(max int) (abundantNumbers []int) {
	for i := 1; i < max; i++ {
		divisors := numberutils.FindDivisors(i)
		var sum int
		for j := range divisors {
			sum += divisors[j]
		}
		sum -= i

		if sum > i {
			abundantNumbers = append(abundantNumbers, i)
		}
	}

	return
}

func Problem23() (sum int) {

	const target = 28124

	abundantNumbers := findAbundantNumbers(target)

	var abundances [target]bool
	for an1 := range abundantNumbers {
		for an2 := 0; an2 <= an1; an2++ {
			combo := abundantNumbers[an1] + abundantNumbers[an2]
			if combo <= target {
				abundances[combo-1] = true
			}
		}
	}

	for i := range abundances {
		if !abundances[i] {
			sum += i + 1
		}
	}

	return
}
