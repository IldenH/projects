// https://gowebexamples.com/hello-world/
package main

import (
  "fmt"
  "net/http"
)

func main() {
  fmt.Println("Hello, world!")

  http.HandleFunc("/", func (w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "Hello, you've requested: %s\n", r.URL.Path)
  })

  http.HandleFunc("/user", func (w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "This is you:\n\n")
    fmt.Fprintf(w, "%s", r.Header.Get("User-Agent"))
  })

  http.ListenAndServe(":8080", nil)
}
