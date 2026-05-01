Backend (FastAPI) for recommender

Setup:
- copy `.env.example` to `.env` and set `MONGODB_URI`
- create a MongoDB instance (local or cloud)
- install dependencies: `pip install -r requirements.txt`
- run: `uvicorn app.main:app --reload --port 8000`

Notes:
- Recommender builds in memory from `items` and `interactions` collections.
- Endpoints: `/users`, `/items`, `/interactions`, `/recommend/{user_id}`, `/similar-items/{item_id}`

Quick demo (MVP):
- Start MongoDB locally or set `MONGODB_URI`.
- Start the backend: `uvicorn app.main:app --reload --port 8000`.
- POST `/admin/seed` to load sample users/items/interactions.
- GET `/recommend/{user_id}` to fetch recommendations.




there should be few things visible on ui:
->there should be reasoning as well for which algo used , its given in ipynb file
->also show the comparision matrix, its given in ipynb
->show user detailes and preferences also for selected user -  from dataset
-> give a search bar alongside dropdown for selecting user
-> enhance the ui to modern and elegant ui designing