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
        self.svd_user = None
        self.svd_movie = None
        self.movie_avg_ratings = {}  # Track average rating per movie
        self.users_df = None  # Store user demographics (age, gender, occupation)

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

            # Fit SVD if sufficient dimensions
            try:
                n_components = min(50, min(pivot.shape) - 1) if min(pivot.shape) > 2 else 2
                svd = TruncatedSVD(n_components=n_components, random_state=42)
                self.svd_user = svd.fit_transform(pivot)
                self.svd_movie = svd.components_.T
            except Exception:
                self.svd_user = None
                self.svd_movie = None

    def _find_similar_users(self, user_id: int, top_k: int = 10) -> List[int]:
        """Find similar users based on age, gender, occupation demographics."""
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
            if other_id == user_id or other_id not in self.user_index:
                continue
            
            score = 0
            # Exact matches get more weight
            if row["gender"] == user_gender and user_gender is not None:
                score += 3
            if row["occupation"] == user_occupation and user_occupation is not None:
                score += 2
            # Age proximity: within 5 years gets 2 points, within 10 years gets 1 point
            if user_age is not None and row["age"] is not None:
                age_diff = abs(row["age"] - user_age)
                if age_diff <= 5:
                    score += 2
                elif age_diff <= 10:
                    score += 1
            
            if score > 0:
                similarities.append((other_id, score))
        
        # Sort by similarity score and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [uid for uid, _ in similarities[:top_k]]

    async def _get_cold_start_recommendations(self, user_id: int, top_n: int = 5) -> List[dict]:
        """For new users: recommend based on similar users' highly-rated movies."""
        rated_items = set()
        if self.user_item_matrix is not None and user_id in self.user_item_matrix.index:
            rated_items = set(self.user_item_matrix.loc[user_id][self.user_item_matrix.loc[user_id] > 0].index.tolist())

        # Find similar users based on demographics
        similar_users = self._find_similar_users(user_id, top_k=10)
        
        if similar_users:
            # Get highly-rated movies from similar users
            movie_scores = {}
            for sim_user in similar_users:
                user_idx = self.user_index.index(sim_user)
                user_ratings = self.user_item_matrix.iloc[user_idx]
                # Get movies rated 4.0 or higher
                high_rated = user_ratings[user_ratings >= 4.0]
                for item_id, rating in high_rated.items():
                    if item_id not in movie_scores:
                        movie_scores[item_id] = []
                    movie_scores[item_id].append(rating)
            
            # Calculate average score for each movie
            if movie_scores:
                avg_scores = {item_id: np.mean(scores) for item_id, scores in movie_scores.items()}
                avg_scores = {item_id: score for item_id, score in avg_scores.items() if item_id not in rated_items}
                sorted_movies = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
                recs = []
                for item_id, avg_rating in sorted_movies[:top_n]:
                    row = self.items_df[self.items_df["item_id"] == item_id]
                    if not row.empty:
                        recs.append({"item_id": int(item_id), "title": row.iloc[0]["title"], "score": float(avg_rating)})
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
        # If user has no interactions -> use demographic-based cold start
        if self.user_item_matrix is None or user_id not in self.user_index:
            # Cold start: get recommendations based on similar users' preferences
            recs = await self._get_cold_start_recommendations(user_id, top_n=top_n)
            if recs:
                return recs
            # Ultimate fallback
            return []

        # If we have SVD factors, use them for personalized recommendations
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

        rated_items = set(top_items)

        scores = np.mean([self.movie_similarity[self.items_df[self.items_df["item_id"] == iid].index[0]] for iid in top_items], axis=0)
        scored = [(int(self.items_df.iloc[i]["item_id"]), float(scores[i])) for i in range(len(scores))]
        scored = [(item_id, score) for item_id, score in scored if item_id not in rated_items]
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
