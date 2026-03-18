# FindMyRepo

FindMyRepo is an AI-assisted platform for discovering open source GitHub repositories through natural language search.

It combines:
- A FastAPI backend for search and repository APIs.
- Gemini for converting user prompts into executable Weaviate queries.
- Weaviate Cloud as the vector and metadata store.
- A React + Vite frontend for search, filtering, and personalized recommendations.

## Core Features
- Natural language repository search.
- Hybrid retrieval using vectors and metadata filters.
- Hidden Gems listing for underrated projects.
- Personalized recommendations based on onboarding preferences.
- Paginated catalog with advanced filtering.

## Technology Stack
- Backend: FastAPI, Pydantic, Weaviate Python Client, Google GenAI SDK.
- Frontend: React, TypeScript, Vite, Tailwind CSS, shadcn/ui.
- Data and embeddings: Weaviate Cloud, sentence-transformers (`all-MiniLM-L6-v2`).

## Project Structure
```
FindMyRepo/
  backend/           # FastAPI service
  frontend/          # React + Vite client
  dataset_test/      # Dataset preparation utilities
  push_to_db.py      # Data ingestion to Weaviate
```

## Prerequisites
- Python 3.11 or newer
- Node.js 18 or newer
- Weaviate Cloud cluster and API key
- Gemini API key

## Environment Setup

Use the provided templates:
- Root template for ingestion: `.env.example`
- Backend template: `backend/.env.example`
- Frontend template: `frontend/.env.example`

### Root `.env` (used by ingestion scripts)
```
WEAVIATE_API_KEY=your_weaviate_api_key
WEAVIATE_URL=https://your-weaviate-cluster.weaviate.network
```

### Backend `backend/.env`
```
GEMINI_API_KEY=your_gemini_api_key
WEAVIATE_API_KEY=your_weaviate_api_key
WEAVIATE_URL=https://your-weaviate-cluster.weaviate.network
```

### Frontend `frontend/.env`
```
VITE_API_BASE_URL=http://localhost:8000
VITE_SEARCH_API_URL=http://localhost:8000/search
VITE_USER_PREFERENCES_API=http://localhost:8000/userpreferences
VITE_ALL_REPOS_ENDPOINT=/allrepos
VITE_HIDDEN_GEMS_ENDPOINT=/hiddengem
```

## Local Development

### 1. Run the backend
```
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Notes:
- All backend Python dependencies are managed in `backend/requirements.txt`.
- Health checks:
  - `GET http://localhost:8000/`
  - `GET http://localhost:8000/health`

### 2. Run the frontend
```
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:8080` by default.

## Docker Setup

This repository includes a Dockerized setup with compatible runtime versions:
- Backend: Python 3.11 (`python:3.11-slim`)
- Frontend build: Node.js 20 (`node:20-alpine`)
- Frontend runtime: Nginx 1.27 (`nginx:1.27-alpine`)

### Run with Docker Compose
From the project root:

```sh
docker compose up --build
```

Access:
- Frontend: `http://localhost:8080`
- Backend API: `http://localhost:8000`

Stop:

```sh
docker compose down
```

### Backend environment variables
The backend service uses:
- `backend/.env`

Make sure this file contains valid values for:
- `GEMINI_API_KEY`
- `WEAVIATE_API_KEY`
- `WEAVIATE_URL`

### Optional frontend endpoint overrides
Frontend URLs are injected at Docker build time using compose build args.

If you want to override defaults:
1. Copy `.env.docker.example` to `.env.docker`
2. Edit values in `.env.docker`
3. Run compose with that env file:

```sh
docker compose --env-file .env.docker up --build
```

## Data Ingestion

To populate Weaviate with repository data:
```
python push_to_db.py
```

Behavior of `push_to_db.py`:
- Connects to Weaviate using `WEAVIATE_URL` and `WEAVIATE_API_KEY`.
- Recreates the `Repos` collection.
- Generates embeddings with `all-MiniLM-L6-v2`.
- Batch inserts records from `github_repos_enriched_final_main.json`.

Important:
- This script deletes and recreates the `Repos` collection before insertion.

## API Overview

Base URL (local): `http://localhost:8000`

- `POST /search`: Natural language search.
- `POST /userpreferences`: Recommendation search from onboarding profile.
- `GET /allrepos`: Paginated repository catalog with filters.
- `GET /hiddengem`: Paginated underrated repositories.
- `GET /example-queries`: Sample prompts.

## Deployment

### Backend (Railway or similar)
- Set service root directory to `backend/`.
- Build command: `pip install -r requirements.txt`
- Start command: `bash start.sh`
- Required environment variables:
  - `GEMINI_API_KEY`
  - `WEAVIATE_API_KEY`
  - `WEAVIATE_URL`

Why `start.sh`:
- It binds to platform-provided `PORT`, which is required for Railway-style hosting.

### Frontend (Vercel)
- Set project root to `frontend/`.
- Build command: `npm run build`
- Output directory: `dist`
- Configure frontend environment variables to point to your deployed backend.
- SPA rewrites are configured in `frontend/vercel.json`.

## Production Considerations
- Restrict CORS in `backend/main.py` to your frontend domain (currently permissive for development).
- Treat all API keys as secrets and store them only in deployment environment settings.
- Review generated-query execution logic before exposing publicly.

## Troubleshooting

If `pip install -r requirements.txt` fails:
- Confirm you are in the `backend/` directory.
- Use Python 3.11+.
- Create and activate a virtual environment before installing.
- Upgrade installer tooling:
```
python -m pip install --upgrade pip setuptools wheel
```
