package datautils

import "../numberutils"

func MakeTriangleFromData(data string) (triangle [][]int) {
	base := 10
	var row []int
	var number int

	for i := range data {
		if data[i] == byte('\n') {
			row = append(row, number)
			triangle = append(triangle, row)
			row = nil
			base = 10
			number = 0
		} else if data[i] == byte(' ') {
			row = append(row, number)
			base = 10
			number = 0
		} else {
			number += base * numberutils.NumberFromByte(data[i])
			base /= 10
		}
	}

	return
}
