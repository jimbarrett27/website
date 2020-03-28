package solutions

import (
	"../numberutils"
)

func Problem21() (sum int) {

	var divisorSums []int

	for i := 1; i < 10000; i++ {
		divisors := numberutils.FindDivisors(i)
		divisorSum := 0
		for j := range divisors {
			divisorSum += divisors[j]
		}
		divisorSum -= i
		divisorSums = append(divisorSums, divisorSum)
	}

	for i := 3; i < 9999; i++ {

		di := divisorSums[i]

		var dj int
		if di < 10000 {
			dj = divisorSums[di-1]
		}

		if dj == i+1 && di != dj {
			sum += di
		}
	}

	return

}
