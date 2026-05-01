from fastapi import APIRouter, HTTPException
from app.db.mongo import get_db
from app.schemas import ItemCreate, ItemUpdate
from typing import List

router = APIRouter()


@router.post("/", status_code=201)
async def create_item(payload: ItemCreate):
    db = get_db()
    count = await db.items.count_documents({})
    doc = payload.dict()
    doc["item_id"] = int(count) + 1
    res = await db.items.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    return doc


@router.get("/", response_model=List[dict])
async def list_items():
    db = get_db()
    cursor = db.items.find()
    items = []
    async for it in cursor:
        it["_id"] = str(it["_id"])
        items.append(it)
    return items


@router.get("/{item_id}")
async def get_item(item_id: int):
    db = get_db()
    item = await db.items.find_one({"item_id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item["_id"] = str(item["_id"])
    return item


@router.put("/{item_id}")
async def update_item(item_id: int, payload: ItemUpdate):
    db = get_db()
    update = {k: v for k, v in payload.dict().items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")
    res = await db.items.update_one({"item_id": item_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    item = await db.items.find_one({"item_id": item_id})
    item["_id"] = str(item["_id"])
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int):
    db = get_db()
    res = await db.items.delete_one({"item_id": item_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {}
