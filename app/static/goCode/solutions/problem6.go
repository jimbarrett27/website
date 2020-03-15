package solutions

func Problem6() int {
	sum := 0
	for i := 0; i < 100; i++ {
		sum += (i + 1)
	}
	squareOfSum := sum * sum
	for i := 0; i < 100; i++ {
		squareOfSum -= ((i + 1) * (i + 1))
	}

	return squareOfSum
}
