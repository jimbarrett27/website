package solutions

import (
	"math/big"
)

func Problem15() int {
	nRoutes := big.NewInt(0)
	nRoutes.Binomial(40, 20)
	return int(nRoutes.Int64())
}
