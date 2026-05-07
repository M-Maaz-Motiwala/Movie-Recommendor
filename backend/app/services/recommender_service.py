import asyncio
import logging
from app.db.mongo import get_db
from app.recommender.model import Recommender


logger = logging.getLogger(__name__)


class RecommenderService:
    def __init__(self):
        self.recommender: Recommender = None
        self._lock = asyncio.Lock()
        self._rebuild_task = None

    async def initialize(self, rebuild: bool = False):
        async with self._lock:
            if self.recommender is None or rebuild:
                logger.info("Initializing recommender rebuild=%s", rebuild)
                db = get_db()
                self.recommender = Recommender(db)
                await self.recommender.fit_from_db()

    def schedule_rebuild(self):
        """Schedule a background rebuild without blocking."""
        try:
            logger.info("Scheduling recommender rebuild")
            self._rebuild_task = asyncio.create_task(self.initialize(rebuild=True))
        except RuntimeError:
            # If no event loop, fall back to sync initialize
            pass

    async def wait_for_rebuild(self):
        """Wait for any in-flight rebuild to complete."""
        if self._rebuild_task and not self._rebuild_task.done():
            try:
                await self._rebuild_task
            except Exception:
                pass  # Ignore errors, recommender is still usable

    async def recommend(self, user_id: int, top_n: int = 5):
        # Wait for any in-flight rebuild before serving recommendations
        await self.wait_for_rebuild()
        # returns list of dicts
        logger.info("Service forwarding recommend request user_id=%s top_n=%s", user_id, top_n)
        return await self.recommender.recommend(user_id, top_n=top_n)

    def get_strategy(self, user_id: int) -> str:
        if not self.recommender:
            return "none"
        logger.info("Service resolving strategy for user_id=%s", user_id)
        return self.recommender.get_strategy(user_id)

    async def similar_items(self, item_id: int, top_n: int = 5):
        await self.wait_for_rebuild()
        return await self.recommender.similar_items(item_id, top_n=top_n)
