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
	case 50:
		return float64(solutions.Problem50())
	default:
		return -1
	}

}

func main() {
}
