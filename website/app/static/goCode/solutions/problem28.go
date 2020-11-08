package solutions

func Problem28() (solution int) {

	sum := 4
	position := 3
	for stepsize := 2; stepsize<1002; stepsize++ {

		position += stepsize

		if stepsize % 2 == 0 {
			sum += position
		} else {
			sum += position-1
		}

		if stepsize == 1001 {
			break
		}

		position += stepsize
		sum += position

	}

	solution = sum

	return
}