import numpy as np
import pandas as pd
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from typing import List


logger = logging.getLogger(__name__)


class Recommender:
    """Lightweight recommender that builds artifacts from MongoDB collections.
    - content-based by genres (TF-IDF)
    - SVD-based latent factors for users/items when enough data
    - demographic-based cold start for new users
    """

    def __init__(self, db):
        self.db = db
        self.tfidf = None
        self.movie_similarity = None
        self.items_df = None
        self.user_item_matrix = None
        self.user_index = None
        self.item_index = None
        self.user_similarity = None
        self.user_means = None
        self.svd_user = None
        self.svd_movie = None
        self.movie_avg_ratings = {}  # Track average rating per movie
        self.users_df = None  # Store user demographics (age, gender, occupation)

    # -----------------------------
    # IMPLEMENTATION HIGHLIGHTS
    # - Content-Based (TF-IDF): builds `self.tfidf` and `self.movie_similarity` from item genres
    # - SVD Matrix Factorization: fits `TruncatedSVD` -> `self.svd_user`, `self.svd_movie`
    # - Demographic Cold-Start: `_find_similar_users` and `_get_cold_start_recommendations`
    # -----------------------------

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

        # Load user demographics (age, gender, occupation)
        users = []
        cursor = self.db.users.find()
        async for u in cursor:
            users.append({
                "user_id": int(u.get("user_id")),
                "age": u.get("age"),
                "gender": u.get("gender"),
                "occupation": u.get("occupation")
            })
        if users:
            self.users_df = pd.DataFrame(users)
        else:
            self.users_df = pd.DataFrame(columns=["user_id", "age", "gender", "occupation"])

        # Build user-item matrix
        ratings = []
        cursor = self.db.interactions.find()
        async for r in cursor:
            ratings.append({
                "user_id": int(r.get("user_id")),
                "item_id": int(r.get("item_id")),
                "rating": float(r.get("rating")) if r.get("rating") is not None else 0.0
            })

        # Calculate average rating per movie for cold start recommendations
        if ratings:
            ratings_df = pd.DataFrame(ratings)
            self.movie_avg_ratings = ratings_df.groupby("item_id")["rating"].mean().to_dict()
            pivot = ratings_df.pivot_table(index="user_id", columns="item_id", values="rating", fill_value=0)
            self.user_item_matrix = pivot
            self.user_index = list(pivot.index)
            self.item_index = list(pivot.columns)

            # Collaborative filtering: mean-center and precompute user-user similarity
            self.user_means = pivot.replace(0, np.nan).mean(axis=1)
            normalized = pivot.copy()
            for user_id in normalized.index:
                mask = normalized.loc[user_id] > 0
                if pd.notna(self.user_means[user_id]):
                    normalized.loc[user_id, mask] -= self.user_means[user_id]
            try:
                self.user_similarity = cosine_similarity(normalized)
            except Exception:
                self.user_similarity = None

            # Fit SVD if sufficient dimensions
            try:
                # --- SVD Matrix Factorization (TruncatedSVD) ---
                # Compute low-rank user/item latent factors for personalized scoring
                n_components = min(50, min(pivot.shape) - 1) if min(pivot.shape) > 2 else 2
                svd = TruncatedSVD(n_components=n_components, random_state=42)
                self.svd_user = svd.fit_transform(pivot)
                self.svd_movie = svd.components_.T
            except Exception:
                self.svd_user = None
                self.svd_movie = None

    def _get_user_rating_count(self, user_id: int) -> int:
        if self.user_item_matrix is None or user_id not in self.user_index:
            return 0
        return int((self.user_item_matrix.loc[user_id] > 0).sum())

    def _choose_strategy(self, user_id: int) -> str:
        num_ratings = self._get_user_rating_count(user_id)
        if num_ratings <= 5:
            strategy = "demographic"
        elif num_ratings < 20:
            strategy = "content"
        elif num_ratings < 70:
            strategy = "svd"
        else:
            strategy = "collaborative"

        logger.info(
            "Selected strategy=%s for user_id=%s rating_count=%s",
            strategy,
            user_id,
            num_ratings,
        )
        return strategy

    async def _recommend_content_based_async(self, user_id: int, top_n: int = 5) -> List[dict]:
        if self.movie_similarity is None or self.items_df is None:
            return []

        logger.info("Calling content-based recommender for user_id=%s top_n=%s", user_id, top_n)

        interactions = []
        cursor = self.db.interactions.find({"user_id": user_id}).sort([("rating", -1)])
        async for r in cursor:
            interactions.append(r)

        top_items = [int(r["item_id"]) for r in interactions[:3]]
        if not top_items:
            return await self._get_cold_start_recommendations(user_id, top_n=top_n)

        rated_items = set(top_items)
        item_indices = []
        for iid in top_items:
            idxs = self.items_df[self.items_df["item_id"] == iid].index
            if len(idxs) > 0:
                item_indices.append(idxs[0])
        if not item_indices:
            return await self._get_cold_start_recommendations(user_id, top_n=top_n)

        scores = np.mean([self.movie_similarity[idx] for idx in item_indices], axis=0)
        scored = [(int(self.items_df.iloc[i]["item_id"]), float(scores[i])) for i in range(len(scores))]
        scored = [(item_id, score) for item_id, score in scored if item_id not in rated_items]
        scored.sort(key=lambda x: x[1], reverse=True)

        results = []
        for item_id, score in scored[:top_n]:
            row = self.items_df[self.items_df["item_id"] == item_id].iloc[0]
            results.append({"item_id": int(item_id), "title": row["title"], "score": float(score)})
        return results

    def _recommend_svd(self, user_id: int, top_n: int = 5) -> List[dict]:
        if self.svd_user is None or self.svd_movie is None or self.user_item_matrix is None or user_id not in self.user_index:
            return []

        logger.info("Calling SVD recommender for user_id=%s top_n=%s", user_id, top_n)

        ui = self.user_index.index(user_id)
        user_factors = self.svd_user[ui]
        preds = user_factors.dot(self.svd_movie.T)
        rated_items = set(self.user_item_matrix.loc[user_id][self.user_item_matrix.loc[user_id] > 0].index.tolist())

        scored = []
        for i, item_id in enumerate(self.item_index):
            if item_id in rated_items:
                continue
            scored.append((int(item_id), float(preds[i])))
        scored.sort(key=lambda x: x[1], reverse=True)

        results = []
        for item_id, score in scored[:top_n]:
            row = self.items_df[self.items_df["item_id"] == item_id].iloc[0]
            results.append({"item_id": int(item_id), "title": row["title"], "score": float(score)})
        return results

    def _recommend_collaborative(self, user_id: int, top_n: int = 5) -> List[dict]:
        if self.user_similarity is None or self.user_item_matrix is None or user_id not in self.user_index:
            return []

        logger.info("Calling collaborative CF recommender for user_id=%s top_n=%s", user_id, top_n)

        user_pos = self.user_index.index(user_id)
        sim_scores = self.user_similarity[user_pos]
        rated_items = set(self.user_item_matrix.loc[user_id][self.user_item_matrix.loc[user_id] > 0].index.tolist())

        predictions = []
        for col_idx, item_id in enumerate(self.item_index):
            if item_id in rated_items:
                continue

            item_ratings = self.user_item_matrix.iloc[:, col_idx].values
            rated_by_others = item_ratings > 0
            if not rated_by_others.any():
                continue

            numerator = float(np.dot(sim_scores[rated_by_others], item_ratings[rated_by_others]))
            denominator = float(np.sum(np.abs(sim_scores[rated_by_others])))
            score = numerator / denominator if denominator > 0 else 0.0
            predictions.append((int(item_id), score))

        predictions.sort(key=lambda x: x[1], reverse=True)
        results = []
        for item_id, score in predictions[:top_n]:
            row = self.items_df[self.items_df["item_id"] == item_id]
            if not row.empty:
                results.append({"item_id": int(item_id), "title": row.iloc[0]["title"], "score": float(score)})
        return results

    def get_strategy(self, user_id: int) -> str:
        return self._choose_strategy(user_id)

    def _find_similar_users(self, user_id: int, top_k: int = 10) -> List[tuple]:
        """Find similar users based on age, gender, occupation demographics.

        Returns a list of (user_id, score) tuples sorted by score descending.
        """
        # --- Demographic Cold-Start Helpers ---
        if self.users_df is None or self.users_df.empty:
            return []

        user_row = self.users_df[self.users_df["user_id"] == user_id]
        if user_row.empty:
            return []

        user_age = user_row.iloc[0]["age"]
        user_gender = user_row.iloc[0]["gender"]
        user_occupation = user_row.iloc[0]["occupation"]

        # Calculate similarity score based on demographics
        similarities = []
        for _, row in self.users_df.iterrows():
            other_id = row["user_id"]
            if other_id == user_id:
                continue

            # Allow similar users that may not yet be in user_index; we'll check ratings later
            score = 0.0
            if row.get("gender") == user_gender and user_gender is not None:
                score += 3.0
            if row.get("occupation") == user_occupation and user_occupation is not None:
                score += 2.0
            if user_age is not None and row.get("age") is not None:
                age_diff = abs(row["age"] - user_age)
                if age_diff <= 5:
                    score += 2.0
                elif age_diff <= 10:
                    score += 1.0

            if score > 0:
                similarities.append((int(other_id), float(score)))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    async def _get_cold_start_recommendations(self, user_id: int, top_n: int = 5) -> List[dict]:
        """For new users: recommend based on similar users' highly-rated movies."""
        # Uses the demographic similarity from `_find_similar_users` to suggest popular
        # items among similar users (or global top-rated items as a fallback).
        rated_items = set()
        if self.user_item_matrix is not None and user_id in self.user_item_matrix.index:
            rated_items = set(self.user_item_matrix.loc[user_id][self.user_item_matrix.loc[user_id] > 0].index.tolist())

        # Find similar users based on demographics
        similar_users = self._find_similar_users(user_id, top_k=10)
        
        if similar_users:
            # Weighted aggregation of ratings from demographically similar users
            numerators = {}  # item_id -> sum(sim * rating)
            denominators = {}  # item_id -> sum(abs(sim))

            for sim_entry in similar_users:
                sim_user_id, sim_score = sim_entry
                # skip similar users without rating history
                if self.user_item_matrix is None or sim_user_id not in self.user_item_matrix.index:
                    continue
                user_idx = self.user_index.index(sim_user_id)
                user_ratings = self.user_item_matrix.iloc[user_idx]
                rated = user_ratings[user_ratings > 0]
                for item_id, rating in rated.items():
                    if int(item_id) in rated_items:
                        continue
                    numerators[item_id] = numerators.get(item_id, 0.0) + sim_score * float(rating)
                    denominators[item_id] = denominators.get(item_id, 0.0) + abs(sim_score)

            # Compute weighted predicted ratings
            predicted = {}
            for item_id, num in numerators.items():
                denom = denominators.get(item_id, 0.0)
                if denom > 0:
                    predicted[item_id] = float(num / denom)

            if predicted:
                # sort by predicted rating
                sorted_movies = sorted(predicted.items(), key=lambda x: x[1], reverse=True)
                recs = []
                for item_id, pred_rating in sorted_movies[:top_n]:
                    row = self.items_df[self.items_df["item_id"] == item_id]
                    if not row.empty:
                        recs.append({"item_id": int(item_id), "title": row.iloc[0]["title"], "score": float(pred_rating)})
                if recs:
                    return recs
        
        # Fallback to globally highest-rated movies if no similar users found
        if self.movie_avg_ratings:
            sorted_movies = sorted(
                ((item_id, score) for item_id, score in self.movie_avg_ratings.items() if item_id not in rated_items),
                key=lambda x: x[1],
                reverse=True,
            )
            recs = []
            for item_id, avg_rating in sorted_movies[:top_n]:
                row = self.items_df[self.items_df["item_id"] == item_id]
                if not row.empty:
                    recs.append({"item_id": int(item_id), "title": row.iloc[0]["title"], "score": float(avg_rating)})
            return recs
        
        return []

    async def recommend(self, user_id: int, top_n: int = 5) -> List[dict]:
        strategy = self._choose_strategy(user_id)

        logger.info("Dispatching recommendation flow user_id=%s strategy=%s top_n=%s", user_id, strategy, top_n)

        if strategy == "demographic":
            recs = await self._get_cold_start_recommendations(user_id, top_n=top_n)
            if recs:
                return recs
        elif strategy == "content":
            recs = await self._recommend_content_based_async(user_id, top_n=top_n)
            if recs:
                return recs
        elif strategy == "svd":
            recs = self._recommend_svd(user_id, top_n=top_n)
            if recs:
                return recs
        elif strategy == "collaborative":
            recs = self._recommend_collaborative(user_id, top_n=top_n)
            if recs:
                return recs

        # Final fallback for sparse data or missing artifacts.
        recs = await self._get_cold_start_recommendations(user_id, top_n=top_n)
        if recs:
            return recs
        return []

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
