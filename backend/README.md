# FindMyRepo — Backend API

FastAPI backend for the FindMyRepo GitHub repository discovery platform. Provides semantic vector search, personalized recommendations, and advanced filtering powered by MongoDB Atlas Vector Search, Google Gemini AI, and `sentence-transformers` embeddings.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Server](#running-the-server)
- [Data Ingestion](#data-ingestion)
- [MongoDB Atlas Setup](#mongodb-atlas-setup)
- [API Reference](#api-reference)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tests](#tests)
- [Troubleshooting](#troubleshooting)

---

## Features

- **Semantic Search** — Queries are embedded with `all-MiniLM-L6-v2` and matched against 43k+ repository embeddings via MongoDB Atlas Vector Search (HNSW, cosine similarity). Returns results ranked by relevance score, filtered to a `0.6` minimum threshold on the frontend.
- **Personalized Recommendations** — Gemini AI maps a structured user profile (role, domains, preferred languages) into a MongoDB filter. Results are then re-ranked by a multi-factor scoring algorithm (language match 40%, domain topics 30%, popularity 20%, recency 10%).
- **Advanced Filtering** — Filter the full repository catalog by language, topics, star/fork range, name/description text, and special categories (Hacktoberfest, GSoC, underrated).
- **Hidden Gems** — Surfaces repositories with 100–1,000 stars that are actively maintained, have a non-empty README, and at least one open issue.
- **Pagination & Sorting** — All list endpoints support page-based pagination and sorting by any supported field.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| Semantic search | MongoDB Atlas Vector Search (HNSW, cosine similarity) |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`, 384 dims) |
| AI recommendations | Google Gemini 2.5 Flash (`google-genai`) |
| Database | MongoDB Atlas |
| Data validation | Pydantic v2 |
| ASGI server | Uvicorn |
| Testing | pytest, mongomock, FastAPI TestClient |

---

## Prerequisites

- Python 3.14+
- A MongoDB Atlas cluster (free tier works)
- A Google Gemini API key — [Get one here](https://aistudio.google.com/app/apikey)
- A GitHub Personal Access Token — [Generate here](https://github.com/settings/tokens) *(required only for data ingestion)*

---

## Installation

```bash
cd backend

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MONGO_URI` | Yes | MongoDB Atlas connection string |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `GITHUB_TOKEN` | Ingestion only | GitHub Personal Access Token |
| `ALLOWED_ORIGINS` | No | Comma-separated frontend origins for CORS. Defaults to `localhost:5173,3000,8080` |
| `HOST` | No | Server host (default: `0.0.0.0`) |
| `PORT` | No | Server port (default: `8000`) |

**MongoDB URI format:**
Atlas → Cluster → Connect → Drivers → copy the string and replace `<password>` with your actual password.

---

## Running the Server

```bash
# Development (auto-reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production (multi-worker)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Once running:
- API base: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Data Ingestion

Populates MongoDB with GitHub repository data — fetches repos via the GitHub API, enriches each with full language lists and a cleaned README, generates a 384-dim embedding, then upserts into MongoDB.

```bash
python ingest_repos.py
```

- Progress is checkpointed to `ingestion_state.json` — interrupted runs resume where they left off.
- GitHub rate limits are respected automatically.
- Requires `GITHUB_TOKEN` and `MONGO_URI` in `.env`.

---

## MongoDB Atlas Setup

### 1. Standard Indexes

Run once after ingestion to enable fast sorting and filtering:

```bash
python scripts/create_indexes.py
```

Or create manually in Atlas Shell / mongosh:

```javascript
use findmyrepo

db.repos.createIndex({ "github_id": 1 }, { unique: true })
db.repos.createIndex({ "stars": -1, "pushed_at": -1 })
db.repos.createIndex({ "pushed_at": -1 })
db.repos.createIndex({ "languages": 1 })
db.repos.createIndex({ "topics": 1 })
db.repos.createIndex({ "name": "text", "description": "text" })
db.repos.createIndex({ "stars": 1, "pushed_at": -1 })
```

### 2. Vector Search Index

Required for `/search`. Must be created manually in the Atlas UI:

1. Atlas → Cluster → **Atlas Search** → **Create Search Index**
2. Select **Atlas Vector Search** → **JSON Editor**
3. Paste this definition:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 384,
      "similarity": "cosine"
    }
  ]
}
```

4. **Name the index `embedding_vector_index`** and save.

> The index name must match exactly. The search service references it as `embedding_vector_index`.

---

## API Reference

### `GET /`
Health ping. Returns `{"status": "ok", "version": "1.0.0"}`.

---

### `GET /health`
Verifies the database connection and returns the total repository count.

```json
{
  "status": "healthy",
  "database": "connected",
  "repositories_count": 43000
}
```

---

### `POST /search`
Semantic repository search using MongoDB Atlas Vector Search.

**Request:**
```json
{
  "query": "beginner-friendly Python projects with good first issues",
  "limit": 100
}
```

`limit` range: 10–150. Default: 60.

**Response:**
```json
{
  "success": true,
  "total_returned": 87,
  "results": [
    {
      "name": "cpython",
      "full_name": "python/cpython",
      "description": "The Python programming language",
      "url": "https://github.com/python/cpython",
      "language": "Python",
      "languages": ["Python", "C"],
      "stars": 62000,
      "forks": 30000,
      "open_issues": 8000,
      "updated_at": "2025-04-01T10:00:00Z",
      "similarity_score": 0.84
    }
  ]
}
```

**How it works:**
1. Query is embedded into a 384-dim vector using `all-MiniLM-L6-v2`.
2. A `$vectorSearch` aggregation pipeline runs against the `embedding_vector_index` (HNSW, cosine similarity).
3. `numCandidates` is set to `limit × 10` to ensure high recall.
4. Each result carries a `similarity_score` from Atlas. The frontend applies a `0.6` minimum threshold before rendering.

---

### `POST /userpreferences`
Returns personalized repository recommendations from a user profile.

**Request:**
```json
{
  "primaryDomains": ["ML / AI / Data Science", "Backend / APIs"],
  "role": "Software Developer / Engineer",
  "expertise": "Medium",
  "preferredLanguages": ["Python", "Go"]
}
```

**Supported values:**

| Field | Options |
|---|---|
| `primaryDomains` | `Frontend / Web`, `Backend / APIs`, `Mobile (iOS/Android)`, `ML / AI / Data Science`, `DevOps / Infrastructure`, `Game Development`, `Cybersecurity` |
| `role` | `Student / Learner`, `Software Developer / Engineer`, `Data Scientist / ML Engineer`, `DevOps / SRE`, `Security Researcher` |
| `expertise` | `Beginner`, `Medium`, `Advanced` |
| `preferredLanguages` | Any language name, e.g. `Python`, `TypeScript`, `Rust` |

**Scoring weights:**

| Factor | Weight |
|---|---|
| Language match | 40% |
| Domain / topic match | 30% |
| Popularity (stars) | 20% |
| Recency (pushed_at) | 10% |

---

### `GET /allrepos`
Paginated catalog with optional filtering and sorting.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | `1` | Page number (min: 1) |
| `limit` | int | `20` | Results per page (max: 100) |
| `sort_by` | string | `stars` | `stars`, `forks`, `updated_at`, `open_issues`, `name` |
| `sort_order` | string | `desc` | `asc` or `desc` |
| `languages` | string | — | Comma-separated, e.g. `Python,Go` |
| `topics` | string | — | Comma-separated, e.g. `cli,devops` |
| `min_stars` / `max_stars` | int | — | Star range |
| `min_forks` / `max_forks` | int | — | Fork range |
| `has_issues` | bool | — | Only repos with open issues |
| `has_wiki` | bool | — | Only repos with a wiki |
| `name_contains` | string | — | Substring match on name (case-insensitive) |
| `description_contains` | string | — | Substring match on description |
| `is_hacktoberfest` | bool | — | Hacktoberfest-tagged repos only |
| `is_gsoc` | bool | — | GSoC-tagged repos only |
| `is_underrated` | bool | — | 50–500 stars, active in last 2 years |

---

### `GET /hiddengem`
Paginated hidden gems feed.

Criteria: 100–1,000 stars, updated within 18 months, non-empty README, at least 1 open issue.

Parameters: `page`, `limit`, `sort_by`, `sort_order` (same constraints as `/allrepos`).

---

### `GET /repo/{owner}/{name}`
Single repository detail including README content.

Returns 404 if the owner/name combination is not found.

---

## Architecture

### Request flow — `/search`

```
User query
  → Embed with all-MiniLM-L6-v2 (384 dims)
  → $vectorSearch aggregation (embedding_vector_index, numCandidates = limit × 10)
  → $addFields: similarity_score ($meta: "vectorSearchScore")
  → Return results with scores
  → Frontend filters score >= 0.6, renders 20 at a time
```

### Request flow — `/userpreferences`

```
User profile (domains, languages, role, expertise)
  → Gemini AI generates MongoDB filter
  → MongoDB returns matching repos
  → Multi-factor preference scoring (language + domain + stars + recency)
  → Return top results sorted by score
```

### Request flow — `/allrepos` and `/hiddengem`

```
Query parameters
  → _build_filter() constructs MongoDB query dict
  → count_documents() for pagination total
  → find().sort().skip().limit() for page slice
  → Return results + pagination metadata
```

---

## Project Structure

```
backend/
├── main.py                  # FastAPI app, all routes, lifespan, CORS
├── models.py                # Pydantic request/response schemas
├── database.py              # MongoDB connection singleton
├── ingest_repos.py          # GitHub data ingestion script
├── requirements.txt
├── .env.example
│
├── services/
│   ├── search.py            # Atlas Vector Search pipeline
│   ├── recommendations.py   # Personalized recommendations + preference scoring
│   └── repository.py        # _build_filter, pagination, hidden gems, get_repo
│
├── utils/
│   ├── gemini_service.py    # Gemini AI client, prompt engineering, output sanitization
│   ├── embeddings.py        # sentence-transformers model wrapper
│   └── helpers.py           # transform_repo_to_response, pagination metadata
│
├── scripts/
│   └── create_indexes.py    # MongoDB standard index creation
│
└── tests/                   # 99 pytest tests
    ├── conftest.py           # mongomock fixtures, sample data
    ├── test_helpers.py
    ├── test_repository.py
    ├── test_search.py
    ├── test_recommendations.py
    └── test_api.py
```

---

## Tests

```bash
pytest tests/ -v
```

99 tests covering:
- `test_helpers.py` — pure function unit tests for response transforms and pagination math
- `test_repository.py` — `_build_filter` logic + DB operations via mongomock
- `test_search.py` — `$vectorSearch` pipeline construction
- `test_recommendations.py` — preference scoring function
- `test_api.py` — all endpoints via FastAPI TestClient with mocked services

---

## Troubleshooting

**`GEMINI_API_KEY not found`**
Ensure `.env` exists in the `backend/` directory and contains `GEMINI_API_KEY`. `load_dotenv()` looks in the same directory as `main.py`.

**`Failed to connect to MongoDB`**
1. Verify `MONGO_URI` is correct and the password has no unescaped special characters (URL-encode `@`, `#`, etc.).
2. In Atlas → **Network Access**, ensure your IP or `0.0.0.0/0` (dev only) is whitelisted.
3. Confirm the cluster is not paused (free-tier clusters pause after 60 days of inactivity).

**CORS error in browser**
Add your frontend origin to `ALLOWED_ORIGINS` in `.env`:
```
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
```

**`/search` returns empty results**
1. `GET /health` — confirm `repositories_count` is non-zero. If zero, run `ingest_repos.py`.
2. Confirm the `embedding_vector_index` exists in Atlas Search and is in **Active** state.
3. Verify documents in MongoDB have an `embedding` field (list of 384 floats).

**Queries are slow**
Run `python scripts/create_indexes.py` to create the standard MongoDB indexes. Without indexes, list endpoints perform full collection scans.

**`Collection objects do not implement truth value testing`**
Use `if collection is None:` instead of `if not collection:` when checking PyMongo collection objects.
