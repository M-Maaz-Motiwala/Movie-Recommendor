from fastapi import APIRouter, HTTPException, Depends
from app.db.mongo import get_db
from app.schemas import UserCreate, UserUpdate
from typing import List
from bson import ObjectId

router = APIRouter()


@router.post("/", status_code=201)
async def create_user(payload: UserCreate):
    db = get_db()
    doc = payload.dict()
    # Using integer user_id auto-increment via count
    count = await db.users.count_documents({})
    doc["user_id"] = int(count) + 1
    res = await db.users.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    return doc


@router.get("/", response_model=List[dict])
async def list_users():
    db = get_db()
    cursor = db.users.find()
    users = []
    async for u in cursor:
        u["_id"] = str(u["_id"])
        users.append(u)
    return users


@router.get("/{user_id}")
async def get_user(user_id: int):
    db = get_db()
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["_id"] = str(user["_id"])
    return user


@router.put("/{user_id}")
async def update_user(user_id: int, payload: UserUpdate):
    db = get_db()
    update = {k: v for k, v in payload.dict().items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")
    res = await db.users.update_one({"user_id": user_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    user = await db.users.find_one({"user_id": user_id})
    user["_id"] = str(user["_id"])
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int):
    db = get_db()
    res = await db.users.delete_one({"user_id": user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {}
