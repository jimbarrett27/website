package solutions

func underTwenty(i int) string {
	switch i {
	case 0:
		return ""
	case 1:
		return "one"
	case 2:
		return "two"
	case 3:
		return "three"
	case 4:
		return "four"
	case 5:
		return "five"
	case 6:
		return "six"
	case 7:
		return "seven"
	case 8:
		return "eight"
	case 9:
		return "nine"
	case 10:
		return "ten"
	case 11:
		return "eleven"
	case 12:
		return "twelve"
	case 13:
		return "thirteen"
	case 14:
		return "fourteen"
	case 15:
		return "fifteen"
	case 16:
		return "sixteen"
	case 17:
		return "seventeen"
	case 18:
		return "eighteen"
	case 19:
		return "nineteen"
	}

	return ""
}

func multiplesOfTen(i int) string {
	switch i {
	case 20:
		return "twenty"
	case 30:
		return "thirty"
	case 40:
		return "forty"
	case 50:
		return "fifty"
	case 60:
		return "sixty"
	case 70:
		return "seventy"
	case 80:
		return "eighty"
	case 90:
		return "ninety"
	}

	return ""
}

func Problem17() (count int) {

	for hundreds := 0; hundreds < 10; hundreds++ {
		for tens := 0; tens < 100; tens += 10 {
			for units := 0; units < 10; units++ {

				i := tens + units
				if i < 20 {
					count += len(underTwenty(i))
				} else {
					count += len(multiplesOfTen(tens)) + len(underTwenty(units))
				}

				if hundreds > 0 {
					count += len(underTwenty(hundreds)) + len("hundred")

					if i != 0 {
						count += len("and")
					}
				}
			}
		}

	}

	count += len("onethousand")

	return

}
