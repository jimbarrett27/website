package solutions

import (
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
)

func getData() (data string) {

	port := os.Getenv("PORT")
	localhost := fmt.Sprintf("http://localhost:%s/project_euler_data/8", port)
	resp, _ := http.Get(localhost)
	defer resp.Body.Close()
	body, _ := ioutil.ReadAll(resp.Body)
	data = string(body)
	return
}

func Problem8() int {

	numberWithLineBreaks := getData()
	var number []int

	for i := range numberWithLineBreaks {
		if numberWithLineBreaks[i] != byte('\n') {
			// convert from uint8 char to actual ordinal
			number = append(number, int(numberWithLineBreaks[i])-48)
		}
	}

	window := 13
	biggestProduct := 1
	for i := 0; i < len(number)-window; i++ {
		product := 1
		for j := i; j < i+window; j++ {
			product *= number[j]
		}
		if product > biggestProduct {
			biggestProduct = product
		}
	}

	return biggestProduct
}
