package main

import (
	"fmt"
	"os"
)

func main() {
	dbPW := os.Getenv("nnr_DB_PW")
	dbHost := os.Getenv("DB_HOST")
	fmt.Println(dbPW)
	fmt.Println(dbHost)
}
