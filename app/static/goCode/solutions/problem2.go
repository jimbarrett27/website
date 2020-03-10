package solutions

func Problem2() (sum int) {

	sum = 0

	var fib1, fib2 = 1, 1
	for {
		var newVal = fib1 + fib2
		if newVal > 4000000 {
			break
		}
		if newVal%2 == 0 {
			sum += newVal
		}

		fib1 = fib2
		fib2 = newVal
	}
	return
}
