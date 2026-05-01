import os
import certifi
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGODB_DB", "recsys_db")

client: AsyncIOMotorClient = None
db = None

async def init_db():
    global client, db
    client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client[MONGO_DB]

def get_db():
    return db
