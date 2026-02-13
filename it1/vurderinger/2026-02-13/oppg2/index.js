async function getBooks() {
  let response = await fetch("https://anapioficeandfire.com/api/books");
  let data = await response.json();
  return data;
}

async function showBooks() {
  let books = await getBooks();
  for (let book of books) {
    let bookEl = document.createElement("article");
    bookEl.className = "book";
    bookEl.textContent = `${book.name}`;
    bookEl.addEventListener("click", () => {
      let isClosed = bookEl.textContent == `${book.name}`;
      bookEl.innerHTML = isClosed ? showInfo(book) : `${book.name}`;
    });
    document.body.appendChild(bookEl);
  }
}

function showInfo(book) {
  return `<b>${book.name}</b>
    <ul>
      <li>Released: <b>${book.released.split("T")[0]}</b></li>
      <li>Pages: <b>${book.numberOfPages}</b></li>
		  <li>ISBN: <b>${book.isbn}</b></li>
      <li>Authors: <b>${book.authors.join(",")}</b></li>
		  <li>Publisher: <b>${book.publisher}</b></li>
      <li>Country: <b>${book.country}</b></li>
		  <li>Media type: <b>${book.mediaType}</b></li>
      <li>Characters: <b>${book.characters.length}</b></li>
    </ul>
  `;
}

showBooks();
