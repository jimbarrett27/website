package solutions

func Problem5() int {

	outerCounter := 0
OUTER:
	for {
		outerCounter += 20
		for i := 0; i < 20; i++ {
			if outerCounter%(i+1) != 0 {
				continue OUTER
			}
		}
		break
	}

	return outerCounter

}
