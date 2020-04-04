package datautils

func AlphabetPosition(c byte) int {

	alphabetUpper := [...]byte{'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'}
	alphabetLower := [...]byte{'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'}

	for i := range alphabetUpper {
		if c == alphabetUpper[i] || c == alphabetLower[i] {
			return i + 1
		}
	}

	panic("Not a valid letter!")

}
