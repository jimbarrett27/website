package numberutils

import (
	"math/big"
)

func BigFibonacci() func() *big.Int {
	previous := big.NewInt(1)
	next := big.NewInt(1)
	ret := new(big.Int)
	oldNext := new(big.Int)
	return func() *big.Int {
		ret = ret.Set(previous)
		oldNext = oldNext.Set(next)
		next = next.Add(next, previous)
		previous = previous.Set(oldNext)
		return ret
	}
}