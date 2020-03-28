package solutions

import (
	"math/big"

	"../numberutils"
)

func Problem20() (sum int) {

	const target int64 = 100

	bigNum := big.NewInt(target)

	for i := int64(2); i < target; i++ {
		mult := big.NewInt(i)
		bigNum.Mul(bigNum, mult)
	}

	sum = numberutils.SumBigNumberDigits(bigNum)

	return

}
