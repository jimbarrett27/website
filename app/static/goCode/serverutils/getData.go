package serverutils

import (
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
)

func GetData(problemNumber int) (data string) {

	port := os.Getenv("PORT")
	localhost := fmt.Sprintf("http://localhost:%s/project_euler_data/%d", port, problemNumber)
	resp, _ := http.Get(localhost)
	defer resp.Body.Close()
	body, _ := ioutil.ReadAll(resp.Body)
	data = string(body)
	return
}
