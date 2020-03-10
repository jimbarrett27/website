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
	default:
		return -1
	}

}

func main() {
}
