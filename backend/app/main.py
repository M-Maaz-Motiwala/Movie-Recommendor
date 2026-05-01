import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.db.mongo import init_db
from app.routes import users, items, recommendations, admin
from app.services.recommender_service import RecommenderService

app = FastAPI(title="Recommender API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await init_db()
    # Initialize recommender and keep in app.state
    rebuild = os.getenv("RECOMMENDER_REBUILD_ON_STARTUP", "false").lower() == "true"
    app.state.recommender = RecommenderService()
    await app.state.recommender.initialize(rebuild=rebuild)


app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(recommendations.router, prefix="", tags=["recommendations"])
app.include_router(admin.router, prefix="", tags=["admin"])


@app.get("/")
def root():
    return {"status": "ok", "service": "recommender"}
