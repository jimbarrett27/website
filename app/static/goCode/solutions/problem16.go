package solutions

import (
	"fmt"
	"math/big"

	"../numberutils"
)

func Problem16() (sum int) {
	bigNum := big.NewInt(0)
	bigNum.Exp(big.NewInt(int64(2)), big.NewInt(int64(1000)), nil)

	bigNumStr := fmt.Sprint(bigNum)
	for i := range bigNumStr {
		sum += numberutils.NumberFromByte(bigNumStr[i])
	}

	return
}
