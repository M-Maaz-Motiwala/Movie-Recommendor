from fastapi import APIRouter, Request, HTTPException
from app.db.mongo import get_db
from app.utils.seed import seed_sample
from app.utils.kaggle_loader import load_movielens_to_mongo
from app.db import mongo as mongo_conf
import asyncio

router = APIRouter()


@router.get("/admin/stats")
async def stats(request: Request):
    db = get_db()
    users = await db.users.count_documents({})
    items = await db.items.count_documents({})
    interactions = await db.interactions.count_documents({})
    return {"users": users, "items": items, "interactions": interactions}


@router.post("/admin/seed")
async def seed(request: Request):
    """Seed database. By default this endpoint downloads MovieLens 100k via Kaggle
    and loads it into MongoDB. This can take a short while on first run.
    """
    # Use configured Mongo settings
    mongo_uri = mongo_conf.MONGO_URI
    mongo_db = mongo_conf.MONGO_DB

    # Run blocking download/insert in thread
    res = await asyncio.to_thread(load_movielens_to_mongo, mongo_uri, mongo_db)

    # trigger recommender rebuild
    recommender = request.app.state.recommender
    if recommender:
        await recommender.initialize(rebuild=True)
    return {"seeded": res}


@router.post("/admin/retrain")
async def retrain(request: Request):
    recommender = request.app.state.recommender
    if not recommender:
        raise HTTPException(status_code=500, detail="Recommender not initialized")
    await recommender.initialize(rebuild=True)
    return {"status": "retrained"}
