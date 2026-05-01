import asyncio

async def seed_sample(db):
    # small sample dataset for MVP demonstration
    users = [
        {"user_id": 1, "name": "Alice", "age": 25, "gender": "F", "preferences": ["Action"]},
        {"user_id": 2, "name": "Bob", "age": 30, "gender": "M", "preferences": ["Comedy"]},
        {"user_id": 944, "name": "TestUser", "age": 28, "gender": "M", "preferences": ["Drama"]},
    ]

    items = [
        {"item_id": 1, "title": "Toy Story (1995)", "genres": "Animation Children Comedy"},
        {"item_id": 5, "title": "GoldenEye (1995)", "genres": "Action Thriller"},
        {"item_id": 50, "title": "Star Wars (1977)", "genres": "Action Sci-Fi"},
        {"item_id": 100, "title": "Fargo (1996)", "genres": "Crime Drama"},
        {"item_id": 200, "title": "L.A. Confidential (1997)", "genres": "Crime Drama"},
    ]

    interactions = [
        {"user_id": 944, "item_id": 1, "rating": 5},
        {"user_id": 944, "item_id": 5, "rating": 4},
        {"user_id": 944, "item_id": 50, "rating": 5},
        {"user_id": 1, "item_id": 1, "rating": 4},
        {"user_id": 2, "item_id": 5, "rating": 3},
    ]

    # clear collections
    await db.users.delete_many({})
    await db.items.delete_many({})
    await db.interactions.delete_many({})

    if users:
        await db.users.insert_many(users)
    if items:
        await db.items.insert_many(items)
    if interactions:
        await db.interactions.insert_many(interactions)

    return {"users": len(users), "items": len(items), "interactions": len(interactions)}
