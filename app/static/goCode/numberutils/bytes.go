package numberutils

func NumberFromByte(char byte) (num int) {

	offsetInt := int(char)

	if offsetInt > 57 || offsetInt < 48 {
		panic("The character isn't in the int range")
	}

	num = int(char) - 48

	return
}
