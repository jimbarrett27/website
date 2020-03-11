package solutions

import (
	"../numberutils"
)

func sumSlice(slice []int) (sum int) {
	sum = 0
	for i := range slice {
		sum += slice[i]
	}
	return
}

func intInSlice(slice []int, num int) bool {
	for i := range slice {
		if slice[i] == num {
			return true
		}
	}

	return false
}

func Problem50() (sum int) {

	targetValue := 1000000

	primes := numberutils.PrimesUpTo(targetValue)

	var oldRow []int
	var olderRow []int
	oldRow = append(oldRow, sumSlice(primes))
	for i := 0; i < len(primes)-1; i++ {

		var newRow []int

		newRow = append(newRow, oldRow[0]-primes[len(primes)-1-i])

		if len(oldRow) > 1 {
			for j := 0; j < len(oldRow)-1; j++ {
				newRow = append(newRow, oldRow[j]+oldRow[j+1]-olderRow[j])
			}
		}
		newRow = append(newRow, oldRow[len(oldRow)-1]-primes[i])

		olderRow = make([]int, len(oldRow))
		copy(olderRow, oldRow)
		oldRow = make([]int, len(newRow))
		copy(oldRow, newRow)

		for j := range newRow {
			if newRow[j] > targetValue {
				break
			}
			if numberutils.IsPrime(primes, newRow[j]) {
				sum = newRow[j]
				return
			}
		}

	}

	return
}
