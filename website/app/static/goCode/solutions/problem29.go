package solutions

import (
	"math"
	"sort"
)

func Problem29() (solution int) {
	terms := []float64{}
	for a:=2; a<101; a++ {
		for b:=2; b<101; b++ {
			terms = append(terms, float64(b)*math.Log(float64(a)))
		}
	}

	sort.Float64s(terms)

	var previousTerm float64
	counter := 0
	for _, term := range terms {

		// put threshold to deal with numerical instability
		if term - previousTerm > 1e-10 {
			counter++
		}
		previousTerm = term
	}

	solution = counter

	return
}