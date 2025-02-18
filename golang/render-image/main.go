package main

import (
  "log"
  "net/http"
)

func handler(w http.ResponseWriter, r *http.Request) {
  w.Header().Set("Content-Type", "text/html")
  http.ServeFile(w, r, "index.html")
}

func imageHandler(w http.ResponseWriter, r *http.Request) {
  w.Header().Set("Content-Type", "image/png")
  http.ServeFile(w, r, "image.png")
}

func main() {
  http.HandleFunc("/", handler)
  http.HandleFunc("/image", imageHandler)

  log.Println("Server started on :8080")
  if err := http.ListenAndServe(":8080", nil); err != nil {
    log.Fatal(err)
  }
}
