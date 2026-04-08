const base_url = "http://127.0.0.1:8000";

const recsEl = document.getElementById("recommendations");
const searchEl = document.getElementById("search");
const resultsEl = document.getElementById("results");
const watchedEl = document.getElementById("watched");

const watched = new Map();

watchedEl.addEventListener("submit", (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  for (const [name, value] of formData) {
    watched.set(name, value);
  }
  console.log(watched);
  updateRecs();
});

let animes = [];

async function addAnimeUser(user_id, anime_id, rating) {
  const response = await fetch(`${base_url}/anime_user/add`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: user_id,
      anime_id: anime_id,
      rating: rating,
    }),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Failed to fetch recommendations");
  }
}

function renderResults(query) {
  const filtered = animes.filter(
    (item) =>
      item.name.toLowerCase().includes(query) &&
      ![...watched.keys()].includes(item.name),
  );
  const results = query ? filtered.slice(0, 20) : [];

  resultsEl.innerHTML = "";
  results.map((item, _) => {
    const btn = document.createElement("button");
    btn.innerHTML = item.name;
    btn.addEventListener("click", () => {
      watched.set(item.name, 1);
      addAnimeUser(1, item.id, 1);
      updateWatched();
      updateRecs();
      renderResults(query);
    });
    resultsEl.appendChild(btn);
  });
  if (results.length == 0 && query != "") {
    resultsEl.innerHTML = "Ingen resultater";
  }
}

let query = "";
searchEl.addEventListener("input", () => {
  query = searchEl.value.toLowerCase().trim();
  renderResults(query);
});

async function getData(endpoint) {
  const response = await fetch(`${base_url}/${endpoint}`);
  return response.json();
}

async function getRecommendations(items, k) {
  const formatted = [...items].map((w, _) => {
    return {
      title: w[0],
      rating: w[1],
    };
  });
  const response = await fetch(`${base_url}/recommend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      watched: formatted,
      top_k: k,
    }),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Failed to fetch recommendations");
  }

  return response.json();
}

async function updateRecs() {
  if ([...watched.keys()].length == 0) {
    recsEl.innerHTML = "Ingenting";
    return;
  }
  let recs = await getRecommendations(watched, 10);
  recs = recs["recommendations"].map((r, _) => {
    return `<li>${r.title}</li>`;
  });
  recsEl.innerHTML = `<ul>${recs.join("")}</ul>`;
}

async function updateWatched() {
  watchedEl.innerHTML = [...watched]
    .map((w, _) => {
      return `
<article class="watchedItem">
  <h4>${w[0]}</h4>
  <img alt="Bilde av ${w[0]}" />
  <input required type="number" min="1" max="10" name="${w[0]}" value="${w[1]}"/>
  <button type="submit">Ok</button>
  <button type="button" class="remove-btn" data-title="${w[0]}">x</button>
</article>`;
    })
    .join("");
  if (watchedEl.innerHTML == "") {
    watchedEl.innerHTML = `Ingenting`;
  }
}

watchedEl.addEventListener("click", (e) => {
  if (e.target.classList.contains("remove-btn")) {
    const title = e.target.dataset.title;
    watched.delete(title);
    updateWatched();
    updateRecs();
    renderResults(query);
  }
});

async function show() {
  let anime_user = await getData("anime_user/1");
  anime_user.map((item, _) => {
    watched.set(item.anime_name, item.rating);
  });

  updateWatched();
  updateRecs();

  animes = await getData("anime");
}

show();
