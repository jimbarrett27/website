package solutions

import (
	"strconv"
)

func isPalindrome(number int) bool {
	s := strconv.Itoa(number)

	for i := range s {
		if s[i] != s[len(s)-(i+1)] {
			return false
		}
	}

	return true
}

func Problem4() (largestPalindrome int) {

	largestPalindrome = 0
	for i := 100; i < 1000; i++ {
		for j := 100; j < i; j++ {
			prod := i * j
			if prod > largestPalindrome && isPalindrome(prod) {
				largestPalindrome = prod
			}
		}
	}

	return
}
