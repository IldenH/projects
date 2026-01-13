async function search(term) {
  let resp = await fetch(
    `https://api.dictionaryapi.dev/api/v2/entries/en/${term}`,
  );
  let data = await resp.json();
  console.log(data);
  return data;
}

function mkList(field, data, el) {
  let vals = data[field];
  if (vals.length == 0) {
    return;
  }

  let section = document.createElement("section");
  el.appendChild(section);
  let title = document.createElement("p");
  title.textContent = field;
  section.appendChild(title);
  for (let val of vals) {
    let itemEl = document.createElement("li");
    itemEl.textContent = val;
    section.appendChild(itemEl);
  }
}

const outputEl = document.getElementById("output");

async function print(term) {
  let data = await search(term);

  for (let p of data) {
    let definition = document.createElement("section");
    outputEl.appendChild(definition);
    let title = document.createElement("h3");
    title.textContent = p["word"];
    definition.appendChild(title);
    for (let meaning of p["meanings"]) {
      let meaningEl = document.createElement("section");
      definition.appendChild(meaningEl);
      let pos = document.createElement("h4");
      pos.textContent = meaning["partOfSpeech"];
      meaningEl.appendChild(pos);

      for (let definition of meaning["definitions"]) {
        let def = document.createElement("li");
        def.textContent = definition["definition"];
        meaningEl.appendChild(def);
      }

      mkList("synonyms", meaning, meaningEl);
      mkList("antonyms", meaning, meaningEl);
    }
  }
}

let searchForm = document.getElementById("search");
searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  let searchterm = e.target["term"].value;
  outputEl.innerHTML = "";
  print(searchterm);
});

print("hello");
