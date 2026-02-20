async function getData(endpoint) {
  const response = await fetch(`http://127.0.0.1:3000/api/${endpoint}`);
  const data = response.json();
  return data;
}

function displayTime(time) {
  const hours = Math.floor(time / 60);
  const mins = time % 60;
  if (hours < 1) {
    return `${mins} minutter`;
  }
  return `${hours} time${hours == 1 ? "" : "r"} og ${mins} minutt${mins == 1 ? "" : "er"}`;
}

function displayImgs(imgs) {
  if (imgs.length == 0) {
    return "";
  }
  return `
<section>
  <h4>Bilder</h4>
<ul>
${imgs.map((img, _) => {
  return `
      <li>
<img src=${img.filnavn} alt=${img.filnavn} />
      ${img.tittel}
      ${img.bildetekst}</li>
`;
})}
</ul>
</section>
`;
}

async function show() {
  const turer = await getData("fjellturer");
  for (let tur of turer) {
    let turEl = document.createElement("article");
    const bilder = await getData("bilder/" + tur.fjelltur_id);
    turEl.innerHTML = `
  <details>
    <summary><strong>${tur.tidspunkt}</strong> - ${tur.fjellnavn}</summary>
    <p>${tur.fornavn} ${tur.etternavn} (${tur.brukernavn} ${tur.epost})</p>
    <section>
    <p><strong>Varighet:</strong> ${displayTime(tur.varighet)}</p>
    <section>
      <h4>Tur</h4>
      <p>${tur.tur_beskrivelse}</p>
    </section>

    <section>
      <h4>Fjell (${tur.hoyde} moh.)</h4>
      <p>${tur.fjell_beskrivelse}</p>
    </section>

    <section>
      <h4>Område: ${tur.omraade_navn}</h4>
      <p>${tur.omraade_beskrivelse}</p>
    </section>
    ${displayImgs(bilder)}
  </details>
`;
    document.body.appendChild(turEl);
  }
}

show();
