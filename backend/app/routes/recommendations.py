from fastapi import APIRouter, HTTPException, Request
import logging
from app.db.mongo import get_db
from app.schemas import Interaction

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/interactions", status_code=201)
async def create_interaction(payload: Interaction, request: Request):
    db = get_db()
    doc = payload.dict()
    await db.interactions.insert_one(doc)
    # Schedule rebuild in background without blocking
    recommender = request.app.state.recommender
    if recommender:
        recommender.schedule_rebuild()
    return {"status": "ok"}


@router.get("/interactions")
async def list_interactions():
    db = get_db()
    cursor = db.interactions.find()
    out = []
    async for it in cursor:
        it["_id"] = str(it["_id"])
        out.append(it)
    return out


@router.get("/recommend/{user_id}")
async def recommend(user_id: int, request: Request, top_n: int = 5):
    recommender = request.app.state.recommender
    if not recommender:
        raise HTTPException(status_code=500, detail="Recommender not initialized")
    logger.info("Received recommend request user_id=%s top_n=%s", user_id, top_n)
    # This will wait for any in-flight rebuild before proceeding
    recs = await recommender.recommend(user_id, top_n=top_n)
    db = get_db()
    interaction_count = await db.interactions.count_documents({"user_id": user_id})
    strategy = recommender.get_strategy(user_id)
    logger.info(
        "Recommend response user_id=%s interaction_count=%s strategy=%s recommendations=%s",
        user_id,
        interaction_count,
        strategy,
        len(recs),
    )
    return {
        "user_id": user_id,
        "recommendations": recs,
        "interaction_count": interaction_count,
        "strategy": strategy,
    }


@router.get("/similar-items/{item_id}")
async def similar_items(item_id: int, request: Request, top_n: int = 5):
    recommender = request.app.state.recommender
    if not recommender:
        raise HTTPException(status_code=500, detail="Recommender not initialized")
    sims = await recommender.similar_items(item_id, top_n=top_n)
    return {"item_id": item_id, "similar": sims}
