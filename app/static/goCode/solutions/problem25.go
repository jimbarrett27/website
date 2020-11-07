package solutions

import (
	"../numberutils"
	"math/big"
)

func Problem25() (solution int) {

	const targetLength int = 1000

	var fibNum *big.Int
	var length int

	index := 0
	fibGenerator := numberutils.BigFibonacci()
	for {
		index++
		fibNum = fibGenerator()
		length = numberutils.CountBigNumberDigits(fibNum)

		if length == targetLength {
			solution = index
			break
		}
	}

	return
}