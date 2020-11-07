package numberutils

import (
	"fmt"
	"math/big"
)

func SumBigNumberDigits(bigNum *big.Int) (sum int) {
	bigNumStr := fmt.Sprint(bigNum)
	for i := range bigNumStr {
		sum += NumberFromByte(bigNumStr[i])
	}
	return
}


func CountBigNumberDigits(num *big.Int) (nDigits int) {
	numStr := fmt.Sprint(num)
	nDigits = len(numStr)
	return
}

func IntSliceToInt(intSlice []int) (value int) {

	value = 0
	decimal := 1
	for i := len(intSlice)-1; i>=0; i-- {
		value += decimal * intSlice[i]
		decimal *= 10
	}

	return
}