import asyncio
from app.db.mongo import get_db
from app.recommender.model import Recommender


class RecommenderService:
    def __init__(self):
        self.recommender: Recommender = None
        self._lock = asyncio.Lock()

    async def initialize(self, rebuild: bool = False):
        async with self._lock:
            if self.recommender is None or rebuild:
                db = get_db()
                self.recommender = Recommender(db)
                await self.recommender.fit_from_db()

    async def recommend(self, user_id: int, top_n: int = 5):
        # returns list of dicts
        return await self.recommender.recommend(user_id, top_n=top_n)

    async def similar_items(self, item_id: int, top_n: int = 5):
        return await self.recommender.similar_items(item_id, top_n=top_n)
