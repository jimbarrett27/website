package main

import "C"

import (
	"./solutions"
)

//export solution
func solution(problemNumber int) float64 {

	switch problemNumber {
	case 1:
		return float64(solutions.Problem1())
	case 2:
		return float64(solutions.Problem2())
	case 3:
		return float64(solutions.Problem3())
	case 4:
		return float64(solutions.Problem4())
	case 5:
		return float64(solutions.Problem5())
	case 6:
		return float64(solutions.Problem6())
	case 7:
		return float64(solutions.Problem7())
	case 8:
		return float64(solutions.Problem8())
	case 9:
		return float64(solutions.Problem9())
	case 10:
		return float64(solutions.Problem10())
	case 11:
		return float64(solutions.Problem11())
	case 12:
		return float64(solutions.Problem12())
	case 13:
		return float64(solutions.Problem13())
	case 50:
		return float64(solutions.Problem50())
	default:
		return 0
	}

}

func main() {
}
