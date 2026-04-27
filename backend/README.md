# FindMyRepo — Backend API

FastAPI backend for the FindMyRepo GitHub repository discovery platform. Provides intelligent natural language search, personalized recommendations, and advanced filtering powered by Google Gemini AI and vector embeddings.

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
- [Troubleshooting](#troubleshooting)

---

## Features

- **Natural Language Search** — Users describe what they need in plain English; Gemini AI translates it into a precise MongoDB filter, combined with vector similarity ranking for relevance.
- **Personalized Recommendations** — Matches repositories to a user's domains, languages, and expertise level using AI-generated queries and a multi-factor scoring algorithm.
- **Advanced Filtering** — Filter the full repository catalogue by language, topics, star range, name/description text, and special categories (Hacktoberfest, GSoC, underrated).
- **Hidden Gems** — Surfaces high-quality repositories with under 1,000 stars that are actively maintained and well-documented.
- **Pagination & Sorting** — All list endpoints support cursor-based pagination and sorting by any supported field.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| AI query generation | Google Gemini 2.5 Flash (`google-genai`) |
| Semantic embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`, 384 dims) |
| Database | MongoDB Atlas |
| Data validation | Pydantic v2 |
| ASGI server | Uvicorn |

---

## Prerequisites

- Python 3.9+
- A MongoDB Atlas cluster
- A Google Gemini API key — [Get one here](https://aistudio.google.com/app/apikey)
- A GitHub Personal Access Token — [Generate here](https://github.com/settings/tokens) (required only for data ingestion)

---

## Installation

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and fill in environment variables
cp .env.example .env
# Edit .env with your credentials (see Environment Variables section below)
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in all required values.

| Variable | Required | Default | Description |
|---|---|---|---|
| `MONGO_URI` | Yes | — | MongoDB Atlas connection string |
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key |
| `GITHUB_TOKEN` | Yes (ingestion only) | — | GitHub Personal Access Token for data ingestion |
| `ALLOWED_ORIGINS` | No | `http://localhost:5173,`<br>`http://localhost:3000,`<br>`http://localhost:8080` | Comma-separated list of frontend origins permitted by CORS |
| `HOST` | No | `0.0.0.0` | Host address for the server |
| `PORT` | No | `8000` | Port for the server |

**Getting your MongoDB URI:**
MongoDB Atlas → Your Cluster → Connect → Drivers → copy the connection string, replacing `<password>` with your actual password.

---

## Running the Server

### Development (with auto-reload)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Standard

```bash
python main.py
```

### Production (multi-worker)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Once running:
- API base: `http://localhost:8000`
- Interactive docs (Swagger UI): `http://localhost:8000/docs`
- Alternative docs (ReDoc): `http://localhost:8000/redoc`

---

## Data Ingestion

The ingestion script populates MongoDB with GitHub repository data. It searches GitHub using a large set of curated queries, enriches each repo with full language lists, cleaned README content, and a vector embedding, then upserts the result into MongoDB.

```bash
python ingest_repos.py
```

**Notes:**
- This is a long-running process. Logs are written to `logs/` automatically.
- Progress is saved to `ingestion_state.json` so interrupted runs can resume where they left off.
- Requires `GITHUB_TOKEN` and `MONGO_URI` to be set in `.env`.
- The script respects GitHub's API rate limits and will pause automatically when limits are approached.

---

## MongoDB Atlas Setup

### 1. Standard Indexes

Run the following in MongoDB Atlas Shell, Compass, or `mongosh`:

```javascript
use findmyrepo

// Deduplication
db.repos.createIndex({ "github_id": 1 }, { unique: true })

// Sorting and pagination
db.repos.createIndex({ "stars": -1, "pushed_at": -1 })
db.repos.createIndex({ "pushed_at": -1 })

// Filtering
db.repos.createIndex({ "languages": 1 })
db.repos.createIndex({ "topics": 1 })

// Text search on name and description
db.repos.createIndex({ "name": "text", "description": "text" })

// Hidden gems query
db.repos.createIndex({ "stars": 1, "pushed_at": -1 })
```

Alternatively, run the automated index creation script:

```bash
python scripts/create_indexes.py
```

### 2. Vector Search Index

The semantic search feature requires a vector search index. This must be created manually in the Atlas UI:

1. Go to Atlas → Your Cluster → **Atlas Search** → **Create Search Index**
2. Select **Atlas Vector Search** → **JSON Editor**
3. Use the following definition:

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

4. Name the index `vector_index` and save.

> Without this index, the `/search` endpoint will still work using the Gemini-generated MongoDB filter alone, but results will not be ranked by semantic similarity.

---

## API Reference

### `GET /`
Health ping. Returns `200 OK` when the server is up.

---

### `GET /health`
Detailed health check. Verifies the database connection and returns the total repository count.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "repositories_count": 15000
}
```

---

### `POST /search`
Natural language repository search using Gemini AI + vector similarity.

**Request body:**
```json
{
  "query": "python machine learning framework for production"
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "name": "mlflow",
      "owner": "mlflow",
      "description": "Open source platform for the ML lifecycle",
      "stars": 18000,
      "languages": ["Python"],
      "topics": ["machine-learning", "mlops"],
      "issues": 452,
      "pushed_at": "2024-11-01T12:00:00Z"
    }
  ]
}
```

**How it works:**
1. The query is embedded into a 384-dimension vector using `all-MiniLM-L6-v2`.
2. Gemini AI generates a MongoDB filter (languages, topics, star range, regex) from the natural language query.
3. MongoDB returns up to 60 candidate repositories matching the filter.
4. Each candidate is scored by cosine similarity against the query embedding.
5. The top 20 results by similarity score are returned.

---

### `POST /userpreferences`
Returns personalized repository recommendations based on user profile.

**Request body:**
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

**How scoring works:**

| Factor | Weight |
|---|---|
| Language match | 40% |
| Domain / topic match | 30% |
| Popularity (stars) | 20% |
| Recency (pushed_at) | 10% |

---

### `GET /allrepos`
Paginated list of all repositories with optional filtering and sorting.

**Query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | `1` | Page number (1-indexed) |
| `limit` | int | `20` | Results per page (max 100) |
| `sort_by` | string | `stars` | Field to sort by. Allowed: `stars`, `forks`, `pushed_at`, `name`, `issues`, `watchers_count` |
| `sort_order` | string | `desc` | `asc` or `desc` |
| `languages` | string | — | Comma-separated language names, e.g. `Python,Go` |
| `topics` | string | — | Comma-separated topic names, e.g. `cli,devops` |
| `min_stars` | int | — | Minimum star count |
| `max_stars` | int | — | Maximum star count |
| `name_contains` | string | — | Substring match on repository name |
| `description_contains` | string | — | Substring match on description |
| `is_hacktoberfest` | bool | — | Only Hacktoberfest-tagged repos |
| `is_gsoc` | bool | — | Only GSoC-tagged repos |
| `is_underrated` | bool | — | Repos with 50–500 stars, updated within 2 years |

**Example:**
```
GET /allrepos?page=1&limit=20&languages=Rust&min_stars=500&sort_by=pushed_at&sort_order=desc
```

---

### `GET /hiddengem`
Paginated list of hidden gem repositories.

Criteria: 100–1,000 stars, updated within the last 18 months, non-empty README, at least 1 open issue.

**Query parameters:** `page`, `limit`, `sort_by`, `sort_order` (same constraints as `/allrepos`).

---

## Architecture

```
┌─────────────────────────────────────────────┐
│                   Client                    │
│              (React Frontend)               │
└─────────────────────┬───────────────────────┘
                      │  HTTP / JSON
                      ▼
┌─────────────────────────────────────────────┐
│              FastAPI  (main.py)             │
│  CORS · Lifespan · Request validation       │
│  Global exception handler                  │
│                                             │
│  POST /search         POST /userpreferences │
│  GET  /allrepos       GET  /hiddengem       │
└──────┬──────────────────────────┬───────────┘
       │                          │
       ▼                          ▼
┌─────────────┐          ┌────────────────────┐
│ SearchService│         │RecommendationService│
│             │          │ RepositoryService  │
│  Embeddings │          │                    │
│  Generator  │          │  Gemini Service    │
└──────┬──────┘          └────────┬───────────┘
       │                          │
       └──────────────┬───────────┘
                      ▼
             ┌────────────────┐
             │  MongoDB Atlas │
             │  (repos)       │
             └────────────────┘
```

### Request flow — `/search`

```
User query
  → Generate 384-dim embedding (sentence-transformers)
  → Generate MongoDB filter via Gemini AI
  → Query MongoDB (up to 60 candidates)
  → Score each candidate by cosine similarity
  → Return top 20 by score
```

### Request flow — `/userpreferences`

```
User profile (domains, languages, expertise)
  → Gemini maps profile to MongoDB query
  → MongoDB returns matching repos
  → Score each repo (language + topic + stars + recency)
  → Return top 20 by preference score
```

### Request flow — `/allrepos` and `/hiddengem`

```
Query parameters
  → Build MongoDB filter (language, topics, stars, flags)
  → Count total matching documents
  → Fetch paginated slice with sort
  → Return results + pagination metadata
```

---

## Project Structure

```
backend/
├── main.py                  # FastAPI app, routes, lifespan, CORS
├── models.py                # Pydantic request/response schemas
├── database.py              # MongoDB connection manager (singleton)
├── ingest_repos.py          # GitHub data ingestion script
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── .env                     # Your credentials (never committed)
│
├── services/
│   ├── search.py            # Hybrid search: Gemini filter + vector similarity
│   ├── recommendations.py   # Personalized recommendations + preference scoring
│   └── repository.py        # Filtering, pagination, hidden gems logic
│
├── utils/
│   ├── gemini_service.py    # Gemini AI client, prompt engineering, output sanitization
│   ├── embeddings.py        # Sentence-transformers model, cosine similarity
│   └── helpers.py           # Response transformation, pagination metadata
│
├── scripts/
│   └── create_indexes.py    # MongoDB index creation utility
│
└── logs/                    # Ingestion log files (auto-created)
```

---

## Troubleshooting

### `ValueError: GEMINI_API_KEY not found in environment variables`
The app will not start without this key. Ensure `.env` exists, contains `GEMINI_API_KEY`, and that `load_dotenv()` can find it (it looks in the same directory as `main.py`).

### `Failed to connect to MongoDB`
1. Verify `MONGO_URI` is correct and the password contains no unescaped special characters.
2. In MongoDB Atlas, go to **Network Access** and ensure your IP (or `0.0.0.0/0` for development) is whitelisted.
3. Confirm the cluster is not paused.

### CORS error in browser
The frontend origin is not in the `ALLOWED_ORIGINS` list. Either add it to `.env`:
```
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
```
Or set it inline when starting the server:
```bash
ALLOWED_ORIGINS="http://localhost:8080" python main.py
```

### `/search` returns empty results
1. Run `GET /health` — confirm `repositories_count` is non-zero. If it is zero, run the ingestion script first.
2. Check that repositories in the database have the `embedding` field populated.
3. Try a broader query term.

### Queries are slow
Ensure MongoDB indexes have been created (see [MongoDB Atlas Setup](#mongodb-atlas-setup)). Without indexes, every query performs a full collection scan.

### `Collection objects do not implement truth value testing`
Use `collection is None` instead of `not collection` when checking PyMongo collection objects. This is already fixed in `database.py`.
