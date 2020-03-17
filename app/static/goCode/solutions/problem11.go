package solutions

import (
	"../numberutils"
	"../serverutils"
)

func prepareGridFromData(data string) (grid [20][20]int) {
	base := 10
	iRow := 0
	iCol := 0
	for i := range data {
		switch data[i] {
		case byte(' '):
			base = 10
			iCol++
		case byte('\n'):
			base = 10
			iCol = 0
			iRow++
		default:
			grid[iRow][iCol] += base * numberutils.NumberFromByte(data[i])
			base /= 10
		}
	}

	return
}

func compareProducts(product int, greatestProduct int) int {
	if product > greatestProduct {
		return product
	}
	return greatestProduct
}

func Problem11() (greatestProduct int) {
	data := serverutils.GetData(11)
	grid := prepareGridFromData(data)

	greatestProduct = 1
	for i := 0; i < 20; i++ {
		for j := 0; j < 20; j++ {

			if i <= 16 {
				product := grid[i][j] * grid[i+1][j] * grid[i+2][j] * grid[i+3][j]
				greatestProduct = compareProducts(product, greatestProduct)
			}

			if j <= 16 {
				product := grid[i][j] * grid[i][j+1] * grid[i][j+2] * grid[i][j+3]
				greatestProduct = compareProducts(product, greatestProduct)
			}

			if i <= 16 && j <= 16 {
				product := grid[i][j] * grid[i+1][j+1] * grid[i+2][j+2] * grid[i+3][j+3]
				greatestProduct = compareProducts(product, greatestProduct)
			}

			if i >= 3 && j <= 16 {
				product := grid[i][j] * grid[i-1][j+1] * grid[i-2][j+2] * grid[i-3][j+3]
				greatestProduct = compareProducts(product, greatestProduct)
			}
		}
	}

	return
}
