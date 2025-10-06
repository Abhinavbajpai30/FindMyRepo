## 🔎 FindMyRepo

An AI-powered search engine and chatbot that helps you discover open-source GitHub repositories using natural language. 🤖 Queries are converted to executable Weaviate searches via Gemini, and results are served through a FastAPI backend to a modern React + Vite frontend.

### ✨ Features
- **🧠 AI-powered search**: Natural language queries (Gemini → Weaviate code)
- **🔎 Hybrid search**: Vector + keyword search over enriched GitHub metadata
- **💎 Hidden Gems**: Underrated repos surfaced with smart filters
- **🎨 Modern UI**: React, Vite, Tailwind, and shadcn/ui

---

## 🏗️ Architecture
- **🧰 Backend (`backend/`)**: FastAPI endpoints for search and catalog. Uses `google-genai` (Gemini) to generate Weaviate query code and executes it against a Weaviate Cloud cluster.
- **🗄️ Vector DB**: Weaviate Cloud collection `Repos` with precomputed embeddings (`sentence-transformers/all-MiniLM-L6-v2`).
- **🧩 Frontend (`frontend/`)**: React + Vite app. Calls the backend `/search` endpoint; falls back to local demo data if unavailable.

---

## ✅ Prerequisites
- 🐍 Python 3.11+
- 🟢 Node.js 18+
- 🗄️ Weaviate Cloud cluster + API key
- 🔑 Gemini API key

---

## 🔐 Environment Variables
Create `.env` files as below.

### 🧰 Backend (`backend/.env`)
```
GEMINI_API_KEY=your_gemini_api_key
WEAVIATE_API_KEY=your_weaviate_api_key
```

The Weaviate cluster URL is configured in `backend/weaviate_service.py`.

### 🧩 Frontend (`frontend/.env`)
```
VITE_SEARCH_API_URL=http://localhost:8000/search
```

---

## 🛠️ Local Development

### 1) 🧰 Backend (FastAPI)
```
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Backend health checks:
- ✅ `GET http://localhost:8000/` → basic health
- ✅ `GET http://localhost:8000/health` → detailed health

### 2) 🧩 Frontend (Vite + React)
```
cd frontend
npm install
npm run dev
```
Vite runs on http://localhost:8080 by default (see `frontend/vite.config.ts`). Ensure `VITE_SEARCH_API_URL` points to your backend `/search` endpoint.

---

## 📦 Optional: Populate Weaviate With Data
To load enriched GitHub repo data into Weaviate, use `push_to_db.py`.

1) Place your dataset JSON at repo root and update the filename in `push_to_db.py` (it expects `github_repos_enriched_final_main_final.json`).
2) Ensure `WEAVIATE_API_KEY` is set in your environment or `.env`.
3) Run:
```
python push_to_db.py
```
This script will:
- 🗂️ Create the `Repos` collection with the expected schema
- 🧮 Generate embeddings with `all-MiniLM-L6-v2`
- 📤 Batch insert objects with vectors

---

## 📡 API Reference (Backend)

Base URL (local): `http://localhost:8000`

### POST `/search` 🔍
Natural language search. Converts your query to Weaviate code via Gemini and executes it.

Request body:
```
{
  "query": "Find popular Python machine learning libraries",
  "limit": 10
}
```

Response (shape excerpt):
```
{
  "success": true,
  "query": "...",
  "results_count": 10,
  "results": [
    {
      "name": "scikit-learn",
      "full_name": "scikit-learn/scikit-learn",
      "description": "...",
      "url": "https://github.com/scikit-learn/scikit-learn",
      "homepage": "",
      "language": "python",
      "languages": ["python", "cython", "c++"],
      "topics": ["machine-learning", "ml", "ai"],
      "stars": 59000,
      "forks": 0,
      "open_issues": 0,
      "license": "",
      "has_issues": true,
      "has_wiki": false,
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "generated_code": "..."  
}
```

### GET `/allrepos` 📚
Paginated catalog with rich filters. Query params include:
- `page` (default 1), `limit` (default 20), `sort_by` (stars|forks|updated_at|created_at|name), `sort_order` (asc|desc)
- Filters: `language`, `languages` (comma-separated), `topics` (comma-separated), `min_stars`, `max_stars`, `min_forks`, `max_forks`, `license`, `has_issues`, `has_wiki`, `is_underrated`, `is_gsoc`, `is_hacktoberfest`, `has_good_first_issues`, `name_contains`, `description_contains`

Example:
```
GET /allrepos?language=python&min_stars=1000&sort_by=stars&sort_order=desc
```

### GET `/hiddengem` 💎
Paginated list of underrated repos. Supports `page`, `limit`, `sort_by`, `sort_order`.

### GET `/example-queries` 🧪
Returns example prompts that work well with the system.

---

## 🎛️ Frontend Notes
- `VITE_SEARCH_API_URL` defaults to `http://localhost:8000/search` if not provided.
- If the backend is unavailable, the Search page falls back to local demo data for a smooth UX.

---

## 🚢 Docker & Deployment

### 🐳 Backend Docker
```
cd backend
docker build -t findmyrepo-api .
docker run --rm -p 8000:8000 --env-file .env findmyrepo-api
```

### 🚆 Railway (Backend)
- Configured via `backend/Dockerfile` and `backend/railway.json`
- Set env vars: `GEMINI_API_KEY`, `WEAVIATE_API_KEY`
- Railway will expose a public URL; use it for the frontend `VITE_SEARCH_API_URL`

### ▲ Vercel (Frontend)
- Deploy `frontend/` as a static Vite app
- Set env var: `VITE_SEARCH_API_URL` to your deployed backend `/search` URL
- `frontend/vercel.json` contains rewrites for SPA routing

---

## 🔒 Security & Notes
- The backend executes generated Weaviate query code within a constrained globals context. Review `backend/gemini_service.py` and `backend/weaviate_service.py` before exposing publicly.
- CORS is open (`*`) in `backend/main.py`; restrict to your frontend origin in production.
- Update the Weaviate cluster URL in `backend/weaviate_service.py` to your own cluster.

---
