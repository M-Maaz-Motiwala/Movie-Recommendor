import os
import kagglehub
import pandas as pd
from pymongo import MongoClient


def load_movielens_to_mongo(mongo_uri: str, mongo_db: str = "recsys_db") -> dict:
    """Download MovieLens 100k via kagglehub and insert into MongoDB.

    Returns a dict with inserted counts.
    """
    path = kagglehub.dataset_download("trishna8/movielens-100k-dataset")

    # locate ml-100k folder
    candidates = [os.path.join(path, "ml-100k"), path]
    base = None
    for c in candidates:
        if os.path.exists(os.path.join(c, "u.data")):
            base = c
            break
    if base is None:
        for root, dirs, files in os.walk(path):
            if "u.data" in files and "u.item" in files and "u.user" in files:
                base = root
                break
    if base is None:
        raise RuntimeError(f"Could not locate MovieLens files under {path}")

    # parse files
    ratings = pd.read_csv(os.path.join(base, "u.data"), sep="\t", names=["user_id", "item_id", "rating", "timestamp"]) 
    users = pd.read_csv(os.path.join(base, "u.user"), sep="|", names=["user_id", "age", "gender", "occupation", "zip"], encoding="latin-1")
    movies_raw = pd.read_csv(os.path.join(base, "u.item"), sep="|", header=None, encoding="latin-1")

    movie_columns = [
        "item_id", "title", "release_date", "video_release_date", "imdb_url",
        "unknown", "Action", "Adventure", "Animation", "Children", "Comedy",
        "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
        "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western"
    ]
    movies_raw.columns = movie_columns
    genre_cols = movie_columns[5:]
    movies_raw["genres"] = movies_raw[genre_cols].apply(lambda r: " ".join([g for g in genre_cols if int(r[g]) == 1]), axis=1)

    items = movies_raw[["item_id", "title", "genres"]].copy()

    # connect to Mongo using pymongo (synchronous)
    client = MongoClient(mongo_uri)
    db = client[mongo_db]

    # clear collections
    db.users.delete_many({})
    db.items.delete_many({})
    db.interactions.delete_many({})

    # build docs
    user_docs = []
    for _, r in users.iterrows():
        user_docs.append({
            "user_id": int(r["user_id"]),
            "name": f"User {int(r['user_id'])}",
            "age": int(r["age"]),
            "gender": str(r["gender"]),
            "occupation": str(r["occupation"]),
            "zip": str(r["zip"]),
            "preferences": [],
        })

    item_docs = []
    for _, r in items.iterrows():
        item_docs.append({
            "item_id": int(r["item_id"]),
            "title": str(r["title"]),
            "genres": str(r["genres"]),
        })

    interaction_docs = []
    for _, r in ratings.iterrows():
        interaction_docs.append({
            "user_id": int(r["user_id"]),
            "item_id": int(r["item_id"]),
            "rating": float(r["rating"]),
            "liked": bool(float(r["rating"]) >= 4.0),
            "timestamp": int(r["timestamp"]),
        })

    if user_docs:
        db.users.insert_many(user_docs)
    if item_docs:
        db.items.insert_many(item_docs)
    if interaction_docs:
        # insert in batches for safety
        batch_size = 5000
        for i in range(0, len(interaction_docs), batch_size):
            db.interactions.insert_many(interaction_docs[i:i+batch_size])

    return {"users": len(user_docs), "items": len(item_docs), "interactions": len(interaction_docs)}
