const base_url = "http://127.0.0.1:8000";

const recsEl = document.getElementById("recommendations");
const searchEl = document.getElementById("search");
const resultsEl = document.getElementById("results");
const watchedEl = document.getElementById("watched");

const watched = [
  {
    title: "Death Note",
    rating: 3,
  },
  {
    title: "Kimi no Na wa.",
    rating: 10,
  },
];

let animes = [];

function renderResults(results) {
  resultsEl.innerHTML = "";
  results.forEach((item) => {
    const li = document.createElement("button");
    li.innerHTML = item;
    resultsEl.appendChild(li);
  });
}

searchEl.addEventListener("input", () => {
  const query = searchEl.value.toLowerCase().trim();
  const filtered = animes.filter((item) => item.toLowerCase().includes(query));
  if (query != "") {
    renderResults(filtered.slice(0, 20));
  } else {
    renderResults("");
  }
});

async function getData(endpoint) {
  const response = await fetch(`${base_url}/${endpoint}`);
  return response.json();
}

async function getRecommendations(watched) {
  const response = await fetch(`${base_url}/recommend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      watched,
      top_k: 10,
    }),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Failed to fetch recommendations");
  }

  return response.json();
}

async function show() {
  watchedEl.innerHTML = watched
    .map((w, _) => {
      return `<article>${w.title} (${w.rating}/10)</article>`;
    })
    .join("");

  let recs = await getRecommendations(watched);
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
