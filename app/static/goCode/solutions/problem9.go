package solutions

func Problem9() (product int) {
OUTER:
	for a := 2; a < 1000; a++ {
		for b := 1; b < a; b++ {
			c := 1000 - a - b
			if (a*a + b*b) == c*c {
				product = a * b * c
				break OUTER
			}
		}
	}

	return
}
