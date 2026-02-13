let codes = ["FOIJRW", "ADDFJF", "VENN26", "SOLDAG", "SMILER", "JIPI67"];

let userinput = document.getElementById("userinput");
let messageEl = document.getElementById("message");

userinput.addEventListener("submit", (e) => {
  e.preventDefault();

  const formData = new FormData(userinput);
  const data = Object.fromEntries(formData.entries());

  messageEl.textContent = showMessage(data);
});

function showMessage(data) {
  let message = `Takk for din registrering, ${data["fornavn"]}!`;
  let okCode = codes.includes(data["rabattkode"].toUpperCase());
  message += okCode
    ? " Du har oppgitt en rabattkode og får en rabattert pris."
    : " Rabattkoden din finnes ikke.";
  return message;
}
