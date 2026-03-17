from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
import numpy as np
import json
from pathlib import Path

path = Path("export")

# ----------------------------
# Load exported recommender data
# ----------------------------

with open(path/"anime_index_to_title.json", "r", encoding="utf-8") as f:
    anime_index_to_title = json.load(f)

with open(path/"anime_title_to_index.json", "r", encoding="utf-8") as f:
    anime_title_to_index = json.load(f)

# shape: [num_anime, embedding_dim]
item_embeddings = np.load(path/"item_embeddings.npy")

# optional but useful if you export them
try:
    item_bias = np.load(path/"item_bias.npy")
except FileNotFoundError:
    item_bias = np.zeros(item_embeddings.shape[0], dtype=np.float32)


# ----------------------------
# FastAPI app
# ----------------------------

app = FastAPI(title="Anime Recommender API")

# Replace with your frontend URL in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# Request / response schemas
# ----------------------------

class RatedAnime(BaseModel):
    title: str
    rating: float = Field(ge=1, le=10)

class RecommendRequest(BaseModel):
    watched: List[RatedAnime]
    top_k: int = Field(default=10, ge=1, le=50)

class Recommendation(BaseModel):
    title: str
    score: float

class RecommendResponse(BaseModel):
    recommendations: List[Recommendation]


# ----------------------------
# Recommender logic
# ----------------------------

def normalize_rating(rating: float) -> float:
    """
    Convert 1-10 rating to a weight centered around neutral.
    Example:
      1 -> -1.0
      5.5 -> ~0
      10 -> +1.0
    """
    return (rating - 5.5) / 4.5


def build_user_vector(watched: List[RatedAnime]) -> tuple[np.ndarray, set[int]]:
    """
    Build a temporary user embedding as a weighted average
    of the embeddings of watched anime.
    """
    vecs = []
    weights = []
    seen_indices = set()

    for entry in watched:
        idx = anime_title_to_index.get(entry.title)
        if idx is None:
            continue

        seen_indices.add(idx)

        weight = normalize_rating(entry.rating)
        vecs.append(item_embeddings[idx])
        weights.append(weight)

    if not vecs:
        raise HTTPException(
            status_code=400,
            detail="None of the provided anime titles were recognized."
        )

    vecs = np.asarray(vecs, dtype=np.float32)
    weights = np.asarray(weights, dtype=np.float32)

    # If all weights are ~0, fall back to equal weighting
    if np.allclose(weights, 0):
        weights = np.ones_like(weights, dtype=np.float32)

    user_vec = np.average(vecs, axis=0, weights=np.abs(weights))

    # Optional: directionally reward liked anime more than disliked anime
    liked_mask = weights > 0
    disliked_mask = weights < 0

    if liked_mask.any():
        liked_vec = np.average(vecs[liked_mask], axis=0, weights=weights[liked_mask])
        user_vec = liked_vec

    if disliked_mask.any():
        disliked_vec = np.average(vecs[disliked_mask], axis=0, weights=np.abs(weights[disliked_mask]))
        user_vec = user_vec - 0.3 * disliked_vec

    return user_vec.astype(np.float32), seen_indices


def score_all_anime(user_vec: np.ndarray) -> np.ndarray:
    """
    Score every anime by dot product with the temporary user vector,
    optionally adding item bias.
    """
    scores = item_embeddings @ user_vec + item_bias
    return scores


def get_top_recommendations(watched: List[RatedAnime], top_k: int) -> List[Recommendation]:
    user_vec, seen_indices = build_user_vector(watched)
    scores = score_all_anime(user_vec)

    # Exclude already watched anime
    if seen_indices:
        scores[list(seen_indices)] = -np.inf

    top_indices = np.argpartition(scores, -top_k)[-top_k:]
    top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

    results = []
    for idx in top_indices:
        results.append(
            Recommendation(
                title=anime_index_to_title[str(int(idx))],
                score=float(scores[idx]),
            )
        )

    return results


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    recs = get_top_recommendations(req.watched, req.top_k)
    return RecommendResponse(recommendations=recs)
