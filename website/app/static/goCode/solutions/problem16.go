package solutions

import (
	"math/big"

	"../numberutils"
)

func Problem16() (sum int) {
	bigNum := big.NewInt(0)
	bigNum.Exp(big.NewInt(int64(2)), big.NewInt(int64(1000)), nil)

	sum = numberutils.SumBigNumberDigits(bigNum)

	return
}
