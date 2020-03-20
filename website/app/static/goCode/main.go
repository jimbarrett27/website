package main

import "C"

import (
	"./solutions"
)

//export solution
func solution(problemNumber int) int {

	switch problemNumber {
	case 1:
		return solutions.Problem1()
	case 2:
		return solutions.Problem2()
	case 3:
		return solutions.Problem3()
	case 4:
		return solutions.Problem4()
	case 5:
		return solutions.Problem5()
	case 6:
		return solutions.Problem6()
	case 7:
		return solutions.Problem7()
	case 8:
		return solutions.Problem8()
	case 9:
		return solutions.Problem9()
	case 10:
		return solutions.Problem10()
	case 11:
		return solutions.Problem11()
	case 12:
		return solutions.Problem12()
	case 13:
		return solutions.Problem13()
	case 14:
		return solutions.Problem14()
	case 15:
		return solutions.Problem15()
	case 50:
		return solutions.Problem50()
	default:
		return 0
	}

}

func main() {
}
