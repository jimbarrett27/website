package solutions

import (
	"../datautils"
	"../serverutils"
)

func Problem67() (maxSum int) {
	data := serverutils.GetData(67)
	triangle := datautils.MakeTriangleFromData(data)

	var sums [][]int
	sums = append(sums, triangle[0])
	for i := range triangle {
		if i == 0 {
			continue
		}
		var newRow []int
		length := len(triangle[i])
		for j := range triangle[i] {
			if j == 0 {
				newRow = append(newRow, triangle[i][0]+sums[i-1][0])
			} else if j == length-1 {
				newRow = append(newRow, triangle[i][j]+sums[i-1][j-1])
			} else {
				sum1 := triangle[i][j] + sums[i-1][j-1]
				sum2 := triangle[i][j] + sums[i-1][j]
				if sum1 > sum2 {
					newRow = append(newRow, sum1)
				} else {
					newRow = append(newRow, sum2)
				}
			}
		}

		sums = append(sums, newRow)
	}

	for i := range sums[len(sums)-1] {
		if sums[len(sums)-1][i] > maxSum {
			maxSum = sums[len(sums)-1][i]
		}
	}

	return

}
