const base_url = "http://127.0.0.1:8000";

const recsEl = document.getElementById("recommendations");
const searchEl = document.getElementById("search");
const resultsEl = document.getElementById("results");
const watchedEl = document.getElementById("watched");

// const watched = [
//   {
//     title: "Death Note",
//     rating: 3,
//   },
//   {
//     title: "Kimi no Na wa.",
//     rating: 10,
//   },
// ];

const watched = new Map();
watched.set("Death Note", 3);
watched.set("Kimi no Na wa.", 10);
watched.set("Gintama", 7);

let animes = [];

function renderResults(results) {
  resultsEl.innerHTML = "";
  results.map((item, _) => {
    const btn = document.createElement("button");
    btn.innerHTML = item;
    btn.addEventListener("click", () => {
      watched.set(item, 1);
      show();
    });
    resultsEl.appendChild(btn);
  });
}

searchEl.addEventListener("input", () => {
  const query = searchEl.value.toLowerCase().trim();
  const filtered = animes.filter((item) => item.toLowerCase().includes(query));
  renderResults(query ? filtered.slice(0, 20) : "");
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

async function show() {
  watchedEl.innerHTML = [...watched]
    .map((w, _) => {
      return `<article>${w[0]} ${w[1]} / 10 <button>✏️ </button></article>`;
    })
    .join("");

  let recs = await getRecommendations(watched, 10);
  console.log(recs);
  recs = recs["recommendations"].map((r, _) => {
    return `<li>${r.title}</li>`;
  });
  recsEl.innerHTML = `<ul>${recs.join("")}</ul>`;

  await fetch("./export/anime_title_to_index.json")
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to load JSON");
      }
      return response.json();
    })
    .then((data) => {
      animes = Object.keys(data);
    })
    .catch((error) => {
      console.error(error);
    });
}

show();
