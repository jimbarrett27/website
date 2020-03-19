package solutions

import (
	"fmt"
	"math"
	"math/big"

	"../numberutils"
	"../serverutils"
)

func Problem13() int {
	data := serverutils.GetData(13)
	var term big.Int
	var exponent int64 = 50
	sum := big.NewInt(0)
	for i := range data {

		if data[i] == byte('\n') {
			exponent = 50
			continue
		}
		t := &term
		t.Exp(big.NewInt(10), big.NewInt(exponent), nil)
		var number int64 = int64(numberutils.NumberFromByte(data[i]))
		t.Mul(t, big.NewInt(number))
		sum.Add(sum, &term)

		exponent--
	}
	ans := fmt.Sprint(sum)
	intSum := 0
	for i := 0; i < 10; i++ {
		intSum += int(math.Pow10(10-i-1)) * numberutils.NumberFromByte(ans[i])
	}
	return intSum

}
