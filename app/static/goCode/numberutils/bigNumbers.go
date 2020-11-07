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