package solutions

func Problem19() (nSundays int) {
	monthLengths := [...]int{31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31}
	var dayCounter int
	for year := 1900; year < 2001; year++ {
		for i := range monthLengths {

			// start on a Monday
			if year > 1900 && dayCounter%7 == 6 {
				nSundays++
			}

			monthLength := monthLengths[i]
			for day := 0; day < monthLength; day++ {
				dayCounter++
			}

			// leap years
			if i == 1 && year%4 == 0 {
				dayCounter++
			}
		}
	}

	return
}
