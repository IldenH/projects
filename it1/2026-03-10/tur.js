import { getData } from "./utils.js";

let usersEl = document.getElementById("users");
let fjellEl = document.getElementById("fjell");
let datoEl = document.getElementById("dato");

async function show() {
  const brukere = await getData("brukere");
  const brukerOpts = brukere.map((b, _) => {
    return `<option value="${b.brukernavn}">${b.fornavn} ${b.etternavn} (${b.brukernavn} ${b.epost})</option>`;
  });
  usersEl.innerHTML = brukerOpts.join("");

  const fjell = await getData("fjell");
  const fjellOpts = fjell.map((f, _) => {
    return `<option value="${f.fjell_id}">${f.fjellnavn}</option>`;
  });
  fjellEl.innerHTML = fjellOpts.join("");
}

document.addEventListener("DOMContentLoaded", () => {
  datoEl.value = new Date().toISOString().slice(0, 10);
});

show();
