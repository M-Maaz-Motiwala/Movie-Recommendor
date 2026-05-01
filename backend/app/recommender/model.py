import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from typing import List


class Recommender:
    """Lightweight recommender that builds artifacts from MongoDB collections.
    - content-based by genres (TF-IDF)
    - SVD-based latent factors for users/items when enough data
    """

    def __init__(self, db):
        self.db = db
        self.tfidf = None
        self.movie_similarity = None
        self.items_df = None
        self.user_item_matrix = None
        self.user_index = None
        self.item_index = None
        self.svd_user = None
        self.svd_movie = None

    async def fit_from_db(self):
        # Load items
        items = []
        cursor = self.db.items.find()
        async for it in cursor:
            items.append({
                "item_id": int(it.get("item_id")),
                "title": it.get("title", ""),
                "genres": it.get("genres", "")
            })
        self.items_df = pd.DataFrame(items)

        if self.items_df.empty:
            # Seed with a tiny default to avoid errors
            self.items_df = pd.DataFrame([
                {"item_id": 1, "title": "Placeholder", "genres": ""}
            ])

        # TF-IDF on genres (guard against empty vocabulary)
        self.tfidf = TfidfVectorizer()
        genres_series = self.items_df["genres"].fillna("").astype(str)
        if genres_series.str.strip().eq("").all():
            genres_series = pd.Series(["unknown"] * len(self.items_df))
        tfidf_matrix = self.tfidf.fit_transform(genres_series)
        self.movie_similarity = cosine_similarity(tfidf_matrix)

        # Build user-item matrix
        ratings = []
        cursor = self.db.interactions.find()
        async for r in cursor:
            ratings.append({
                "user_id": int(r.get("user_id")),
                "item_id": int(r.get("item_id")),
                "rating": float(r.get("rating")) if r.get("rating") is not None else 0.0
            })

        if ratings:
            ratings_df = pd.DataFrame(ratings)
            pivot = ratings_df.pivot_table(index="user_id", columns="item_id", values="rating", fill_value=0)
            self.user_item_matrix = pivot
            self.user_index = list(pivot.index)
            self.item_index = list(pivot.columns)

            # Fit SVD if sufficient dimensions
            try:
                n_components = min(50, min(pivot.shape) - 1) if min(pivot.shape) > 2 else 2
                svd = TruncatedSVD(n_components=n_components, random_state=42)
                self.svd_user = svd.fit_transform(pivot)
                self.svd_movie = svd.components_.T
            except Exception:
                self.svd_user = None
                self.svd_movie = None

    async def recommend(self, user_id: int, top_n: int = 5) -> List[dict]:
        # If user has no interactions -> content-based using preferences if present
        if self.user_item_matrix is None or user_id not in self.user_index:
            # fallback: return top similar to popular or empty
            # Use genre-based popularity
            top_idxs = list(np.argsort(-self.movie_similarity.mean(axis=0))[:top_n])
            recs = []
            for idx in top_idxs:
                row = self.items_df.iloc[idx]
                recs.append({"item_id": int(row["item_id"]), "title": row["title"], "score": float(self.movie_similarity.mean(axis=0)[idx])})
            return recs

        # If we have SVD factors, use them
        if self.svd_user is not None and self.svd_movie is not None and user_id in self.user_index:
            ui = self.user_index.index(user_id)
            user_factors = self.svd_user[ui]
            preds = user_factors.dot(self.svd_movie.T)
            # mask already rated
            rated_items = set(self.user_item_matrix.loc[user_id][self.user_item_matrix.loc[user_id] > 0].index.tolist())
            scored = []
            for i, item in enumerate(self.item_index):
                if item in rated_items:
                    continue
                scored.append((item, preds[i]))
            scored.sort(key=lambda x: x[1], reverse=True)
            top = scored[:top_n]
            if not top:
                # Fall back to content-based scoring over full catalog
                rated_catalog_idx = self.items_df[self.items_df["item_id"].isin(list(rated_items))].index.tolist()
                if rated_catalog_idx:
                    content_scores = self.movie_similarity[rated_catalog_idx].mean(axis=0)
                    top_candidates = []
                    for i in range(len(self.items_df)):
                        iid = int(self.items_df.iloc[i]["item_id"])
                        if iid in rated_items:
                            continue
                        top_candidates.append((iid, float(content_scores[i])))
                    top_candidates.sort(key=lambda x: x[1], reverse=True)
                    top = top_candidates[:top_n]
            results = []
            for item_id, score in top:
                row = self.items_df[self.items_df["item_id"] == item_id].iloc[0]
                results.append({"item_id": int(item_id), "title": row["title"], "score": float(score)})
            return results

        # Fallback: content-based using user's highest-rated items in interactions
        interactions = []
        cursor = self.db.interactions.find({"user_id": user_id}).sort([("rating", -1)])
        async for r in cursor:
            interactions.append(r)
        top_items = [int(r["item_id"]) for r in interactions[:3]]
        if not top_items:
            return []

        scores = np.mean([self.movie_similarity[self.items_df[self.items_df["item_id"] == iid].index[0]] for iid in top_items], axis=0)
        scored = [(int(self.items_df.iloc[i]["item_id"]), float(scores[i])) for i in range(len(scores))]
        scored.sort(key=lambda x: x[1], reverse=True)
        results = []
        for item_id, score in scored[:top_n]:
            row = self.items_df[self.items_df["item_id"] == item_id].iloc[0]
            results.append({"item_id": int(item_id), "title": row["title"], "score": float(score)})
        return results

    async def similar_items(self, item_id: int, top_n: int = 5) -> List[dict]:
        if self.movie_similarity is None:
            return []
        # find index
        idxs = self.items_df[self.items_df["item_id"] == item_id].index
        if len(idxs) == 0:
            return []
        idx = idxs[0]
        sims = list(enumerate(self.movie_similarity[idx]))
        sims = [(i, s) for i, s in sims if i != idx]
        sims.sort(key=lambda x: x[1], reverse=True)
        results = []
        for i, s in sims[:top_n]:
            row = self.items_df.iloc[i]
            results.append({"item_id": int(row["item_id"]), "title": row["title"], "score": float(s)})
        return results
