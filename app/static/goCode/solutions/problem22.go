package solutions

import (
	"sort"

	"strings"

	"../datautils"
	"../serverutils"
)

func Problem22() (sum int) {

	data := serverutils.GetData(22)

	names := strings.Split(data[1:len(data)-1], "\",\"")

	sort.Strings(names)

	for i := range names {
		score := 0
		for j := range names[i] {
			score += datautils.AlphabetPosition(names[i][j])
		}

		score *= (i + 1)

		sum += score
	}

	return
}
