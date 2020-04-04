package solutions

import (
	"../numberutils"
	"../serverutils"
)

func Problem8() int {

	numberWithLineBreaks := serverutils.GetData(8)
	var number []int

	for i := range numberWithLineBreaks {
		if numberWithLineBreaks[i] != byte('\n') {
			// convert from uint8 char to actual ordinal
			number = append(number, numberutils.NumberFromByte(numberWithLineBreaks[i]))
		}
	}

	window := 13
	biggestProduct := 1
	for i := 0; i < len(number)-window; i++ {
		product := 1
		for j := i; j < i+window; j++ {
			product *= number[j]
		}
		if product > biggestProduct {
			biggestProduct = product
		}
	}

	return biggestProduct
}
