package solutions

import (
	"../numberutils"
)

func Problem12() (triangleNumber int) {

	triangleNumber = 1
	i := 1
	for {
		i++
		triangleNumber += i

		divisors := numberutils.FindDivisors(triangleNumber)

		if len(divisors) > 500 {
			return
		}
	}
}
