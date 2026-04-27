const recsEl = document.getElementById("recommendations");
const searchEl = document.getElementById("search");
const resultsEl = document.getElementById("results");
const watchedEl = document.getElementById("watched");
const usernameEl = document.getElementById("username");
const usersEl = document.getElementById("users");

const watched = new Map();
let active_user = 1;

watchedEl.addEventListener("change", (e) => {
  if (e.target.tagName === "SELECT") {
    const id = e.target.name;
    const value = e.target.value;

    const existing = watched.get(Number(id));
    if (existing) {
      watched.set(Number(id), { ...existing, rating: value });
    }

    fetchAnimeUser("PUT", active_user, id, value);
    updateWatched();
    updateRecs();
  }
});

let animes = [];
let animeMap = new Map();

async function fetchAnimeUser(method, user_id, anime_id, rating) {
  const response = await fetch("/anime_user", {
    method: method,
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
    throw new Error(err.detail || "Failed to fetch User_Anime");
  }
}

function scoreMatch(name, query) {
  name = name.toLowerCase();
  query = query.toLowerCase();

  if (!query) return 0;
  if (name === query) return 1000;
  if (name.startsWith(query)) return 500 - name.length;
  const index = name.indexOf(query);
  if (index !== -1) return 300 - index;

  // Fuzzyfinding
  let score = 0;
  let qi = 0;
  for (let i = 0; i < name.length && qi < query.length; i++) {
    if (name[i] === query[qi]) {
      score += 10;
      qi++;
    }
  }

  if (qi === 0) return -100;
  if (qi < query.length) {
    score -= (query.length - qi) * 20;
  }

  return score;
}

function renderResults(query) {
  const watchedNames = new Set([...watched.values()].map((val) => val.name));

  const results = query
    ? animes
        .map((item) => ({
          item,
          score: scoreMatch(item.name, query),
        }))
        .filter(({ item, score }) => score > 0 && !watchedNames.has(item.name))
        .sort((a, b) => b.score - a.score)
        .slice(0, 10)
        .map(({ item }) => item)
    : [];

  resultsEl.innerHTML = "";
  results.map((item, _) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.innerHTML = item.name;
    btn.setAttribute("aria-label", `Legg til ${item.name}`);
    btn.addEventListener("click", () => {
      watched.set(item.id, {
        name: item.name,
        picture: item.picture,
        rating: 1,
      });
      fetchAnimeUser("POST", active_user, item.id, 1);
      updateWatched();
      updateRecs();
      renderResults(query);

      setTimeout(() => {
        const el = watchedEl.querySelector(`[data-id="${item.id}"]`);
        if (el) {
          el.focus();
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 0);
    });
    li.appendChild(btn);
    resultsEl.appendChild(li);
  });
  if (results.length == 0 && query != "") {
    resultsEl.innerHTML = "";
    const li = document.createElement("li");
    li.textContent = "Ingen resultater";
    li.setAttribute("role", "status");
    resultsEl.appendChild(li);
  }
}

let query = "";
searchEl.addEventListener("input", () => {
  query = searchEl.value.toLowerCase().trim();
  renderResults(query);
});

async function getData(endpoint) {
  const response = await fetch(`/${endpoint}`);
  return response.json();
}

async function getRecommendations(items, k) {
  const formatted = [...items].map((w, _) => {
    return {
      title: w[1].name,
      rating: w[1].rating,
    };
  });
  const response = await fetch("/recommend", {
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
  recs = recs.recommendations.map((r, _) => {
    return `<li>${r.title}</li>`;
  });
  recsEl.innerHTML = `<ul>${recs.join("")}</ul>`;
}

async function updateWatched() {
  watchedEl.innerHTML = [...watched]
    .map((w, _) => {
      return `
<li class="watchedItem" data-id="${w[0]}" tabindex="-1">
  <h4>${w[1].name}</h4>
  <button type="button" class="remove-btn" data-id="${w[0]}" data-title="${w[1].name}" aria-label="Fjern ${w[1].name}">&times;</button>
  <img alt="Bilde av ${w[1].name}" src="${w[1].picture}"/>
  <div class="select-wrapper">
    <select name="${w[0]}" required aria-label="Rangering for ${w[1].name}">
      ${Array.from({ length: 10 }, (_, i) => {
        const val = i + 1;
        return `<option value="${val}" ${val === Number(w[1].rating) ? "selected" : ""}>${val}</option>`;
      }).join("")}
    </select>
  </div>
</li>`;
    })
    .join("");
  if (watchedEl.innerHTML == "") {
    watchedEl.innerHTML = `Ingenting`;
  }
}

watchedEl.addEventListener("click", (e) => {
  if (e.target.classList.contains("remove-btn")) {
    const confirmed = window.confirm(
      `Vil du fjerne "${e.target.dataset.title}"?`,
    );
    if (!confirmed) return;

    const id = e.target.dataset.id;
    watched.delete(Number(id));
    fetchAnimeUser("DELETE", active_user, id);
    updateWatched();
    updateRecs();
    renderResults(query);
  }
});

usersEl.addEventListener("change", (e) => {
  active_user = e.target.value;
  getWatched();
  updateUser();
});

async function getWatched() {
  let anime_user = await getData(`anime_user/${active_user}`);
  watched.clear();
  anime_user.map((item, _) => {
    let anime = animeMap.get(item.anime_id);
    watched.set(item.anime_id, {
      name: anime.name,
      picture: anime.picture,
      rating: item.rating,
    });
  });
  updateWatched();
  updateRecs();
}

async function updateUser() {
  let user = await getData(`user/${active_user}`);
  usernameEl.textContent = `Hei ${user.name}!`;
}

async function show() {
  animes = await getData("anime");
  animeMap = new Map(animes.map((a) => [Number(a.id), a]));

  let users = await getData("user");
  usersEl.innerHTML = users.map(
    (u, _) => `<option value="${u.id}">${u.name}</option>`,
  );
  updateUser();
  getWatched();
}

show();
