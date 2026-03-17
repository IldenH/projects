const base_url = "http://127.0.0.1:8000";

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

console.log(getData("health"));
