package solutions

import (
	"../numberutils"
)

func Problem24() (solution int) {
	
	target_ind := 1000000
	numbers := []int{0,1,2,3,4,5,6,7,8,9}

	counter := 0

	var solution_slice []int
	var permute func([]int, []int)
	permute = func(remaining []int, permutation []int) () {
		
		if len(remaining) == 0 {
			counter++
			if counter == target_ind {
				solution_slice = permutation
			}
			return
		}
		
		for i := 0 ; i<len(remaining); i++ {

			x := make([]int, len(remaining))
			copy(x, remaining)
			x = append(x[:i], x[i+1:]...)

			y := append(permutation, remaining[i])
			permute(x, y)
		}
		
	}
	permute(numbers, []int{})

	solution = numberutils.IntSliceToInt(solution_slice)

	return
}