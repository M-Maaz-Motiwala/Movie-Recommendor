# Movie Recommender System

A full-stack web application that provides personalized movie recommendations using a hybrid recommendation engine. The project features a FastAPI backend with MongoDB and a modern React (Vite) frontend.

## Overview

This project implements a recommendation engine that dynamically builds its model based on data stored in MongoDB. The system can provide tailored movie recommendations for specific users based on their past interactions, as well as suggest similar items using content features.

### Tech Stack

**Backend:**
- **Framework:** FastAPI
- **Database:** MongoDB (using Motor for async operations)
- **Machine Learning / Data Processing:** `scikit-learn`, `pandas`, `numpy`

**Frontend:**
- **Framework:** React (bootstrapped with Vite)
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios

### Recommendation Engine Algorithm

The core logic resides in a lightweight recommendation model that builds artifacts directly from the database collections. It employs a **Hybrid Approach** leveraging three recommendation algorithms:
1. **Content-Based Filtering:** Uses TF-IDF vectorization on movie genres to compute cosine similarity between items. This serves as a strong baseline, especially for new items or users without prior interaction history.
2. **Collaborative Filtering:** Analyzes user-item interactions to find similarities and patterns among user behaviors to generate recommendations.
3. **Matrix Factorization:** Applies Singular Value Decomposition (`TruncatedSVD`) on the interaction matrix when there is sufficient data (based on user count and interactions) to capture latent user preferences and item characteristics.

The algorithmic reasoning, comparisons, and performance metrics are documented in the accompanying Jupyter Notebook (`rs-project-bai-6a.ipynb`).

## Features

- **RESTful API:** Endpoints to manage users, items, and interactions.
- **Recommendation Endpoints:** Get personalized top-N movie recommendations for a user or fetch similar movies based on a specific item ID.
- **Admin Panel:** Seed the database with sample users, items, and interaction datasets.
- **Interactive Dashboard:** Select users to view their personalized movie suggestions.

## Planned Enhancements (UI/UX)

The frontend interface is slated for modern and elegant UI/UX improvements, including:
- Displaying the underlying reasoning for the chosen algorithm directly on the UI (based on notebook findings).
- Showcasing the comparison matrix from the research phase.
- Displaying detailed user preferences and information from the dataset for the selected user.
- Adding a search bar alongside the dropdown for an enhanced user selection experience.
- Overhauling the visual aesthetics to meet modern design standards.

## Setup Instructions

### Backend
1. Navigate to the `backend/` directory.
2. Copy `.env.example` to `.env` and set your `MONGODB_URI`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Run the development server: `uvicorn app.main:app --reload --port 8000`.

### Frontend
1. Navigate to the `frontend/` directory.
2. Install dependencies: `npm install`.
3. Run the development server: `npm run dev`.
