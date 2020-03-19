package solutions

func Problem14() (startingNumber int) {

	const max = 1000000

	var sequenceLengths [max]int

	for i := 10; i < max; i++ {
		number := i
		for {
			if number == 1 {
				break
			}
			if number < max && sequenceLengths[number] != 0 {
				sequenceLengths[i] += sequenceLengths[number]
				break
			}
			if number%2 == 0 {
				number /= 2
				sequenceLengths[i]++
			} else {
				number = 3*number + 1
				sequenceLengths[i]++
			}
		}
	}

	maxLength := 0
	var corrNumber int
	for i := 0; i < 1000000; i++ {
		if sequenceLengths[i] > maxLength {
			maxLength = sequenceLengths[i]
			corrNumber = i
		}
	}

	return corrNumber

}
