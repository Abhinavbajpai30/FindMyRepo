<div align="center">

# 🔎 FindMyRepo

![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=flat-square&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi)
![MongoDB](https://img.shields.io/badge/MongoDB_Atlas-47A248?style=flat-square&logo=mongodb&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_AI-4285F4?style=flat-square&logo=google&logoColor=white)

**An AI-powered platform for discovering open-source GitHub repositories through semantic natural language search.**

</div>

---

## 🎬 Demo

<p align="center">
  <img src="assets/demo.gif" alt="FindMyRepo demo" width="800" />
</p>

---

## ✨ Core Features

- 🧠 **Semantic Search** — Describe what you need in plain English. Atlas Vector Search finds the most relevant repositories across a corpus of 43k+ repos using cosine similarity on 384-dimension embeddings.
- 🎯 **Personalized Recommendations** — Onboard with your role, expertise, and preferred languages. Gemini AI maps your profile to a multi-factor scoring algorithm covering language match, domain relevance, popularity, and recency.
- 💎 **Hidden Gems** — A curated feed of high-quality, under-1k-star repositories that are actively maintained and well-documented — repos you won't find on any trending page.
- 🎃 **Hacktoberfest Explorer** — Dedicated page to browse Hacktoberfest-tagged repos with advanced filters for first-time contributors.
- 🔖 **Saved Repos** — Bookmark any repository locally. Your collection persists across sessions via `localStorage`.
- 🔗 **Shareable Search URLs** — Every search syncs to the browser URL (`?q=your+query`). Share a link and your recipients land on the same results.
- ♾️ **Relevance-Filtered Infinite Scroll** — Results stream in 20 at a time. Only repositories above a cosine similarity threshold are shown; the feed ends naturally when relevance drops.
- 🧭 **Advanced Filtering** — Filter the full catalog by language, topics, star range, fork range, name, description, and special categories (GSoC, Hacktoberfest, underrated).

---

## 🏗 Architecture & Engineering Decisions

### System Diagram

<p align="center">
  <img src="assets/architecture.png" alt="FindMyRepo system architecture" width="800" />
</p>

### Key Engineering Decisions

**MongoDB Atlas Vector Search (HNSW)**
Search was originally backed by Weaviate and a Gemini-generated MongoDB filter. The filter approach limited coverage to repos with exact matching topic tags — as few as 28 results from 43k. Migrating to Atlas Vector Search's HNSW index on the `embedding` field (384-dim cosine similarity) queries the full corpus semantically, consistently returning 60–100 relevant results without any filter generation overhead.

**`all-MiniLM-L6-v2` Embeddings**
Each repository is embedded as a concatenation of its title, primary language, topics, and README excerpt. At inference time, the user query is embedded with the same model. The 384-dimension space is large enough for strong semantic resolution while remaining fast enough to embed queries in under 100ms on CPU.

**Gemini AI — Scoped to `/userpreferences` Only**
Gemini is deliberately kept out of the search path after the Vector Search migration. It is retained exclusively for the `/userpreferences` endpoint, where it maps a structured user profile (role, domains, languages) into a MongoDB filter for personalized recommendations. Isolating AI generation to structured inputs reduces latency and eliminates the risk of hallucinated search filters.

**Relevance Cutoff on the Frontend**
Each search result carries a `similarity_score` (0–1) from Atlas Vector Search. The frontend filters out results below `0.6` and renders the rest in batches of 20 via IntersectionObserver. This means the page ends organically when the results are no longer meaningfully relevant — without any hard-coded result cap visible to the user.

---

## 💻 Tech Stack

| Component | Technology |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, React Query |
| **Backend** | FastAPI, Pydantic v2, Uvicorn |
| **AI / Search** | MongoDB Atlas Vector Search (HNSW), `sentence-transformers` (`all-MiniLM-L6-v2`), Google Gemini AI |
| **Database** | MongoDB Atlas |
| **Testing** | pytest, mongomock, FastAPI TestClient · Vitest, Testing Library |

---

## 📂 Project Structure

```
FindMyRepo/
├── backend/                 # FastAPI service
│   ├── main.py              # Routes, lifespan, CORS
│   ├── models.py            # Pydantic schemas
│   ├── database.py          # MongoDB connection singleton
│   ├── ingest_repos.py      # GitHub data ingestion script
│   ├── requirements.txt
│   ├── services/
│   │   ├── search.py        # Atlas Vector Search pipeline
│   │   ├── recommendations.py
│   │   └── repository.py    # Filtering, pagination, hidden gems
│   ├── utils/
│   │   ├── gemini_service.py
│   │   ├── embeddings.py
│   │   └── helpers.py
│   ├── scripts/
│   │   └── create_indexes.py
│   └── tests/               # pytest suite (99 tests)
│
└── frontend/                # React + Vite client
    ├── src/
    │   ├── pages/           # Home, Search, AllRepos, HiddenGems,
    │   │   │                #   Hacktoberfest, Saved, Onboarding
    │   ├── components/      # Navbar, RepoCard, ErrorBoundary, …
    │   ├── contexts/        # BookmarksContext, PreferencesContext
    │   ├── lib/             # api.ts, transforms.ts, utils.ts
    │   └── __tests__/       # Vitest suite (27 tests)
    └── public/
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.14+
- Node.js 18+
- MongoDB Atlas cluster (free tier works)
- Google Gemini API key — [Get one here](https://aistudio.google.com/app/apikey)
- GitHub Personal Access Token — [Generate here](https://github.com/settings/tokens) *(ingestion only)*

### ⚙️ Environment Variables

<details>
<summary><b>Backend — <code>backend/.env</code></b></summary>

```env
MONGO_URI=mongodb+srv://<user>:<pass>@cluster0.xxxxx.mongodb.net/?appName=Cluster0
GEMINI_API_KEY=your_gemini_api_key
GITHUB_TOKEN=github_pat_...          # ingestion only
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
HOST=0.0.0.0
PORT=8000
```
</details>

<details>
<summary><b>Frontend — <code>frontend/.env</code></b></summary>

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SEARCH_API_URL=http://localhost:8000/search
VITE_USER_PREFERENCES_API=http://localhost:8000/userpreferences
VITE_ALL_REPOS_ENDPOINT=/allrepos
VITE_HIDDEN_GEMS_ENDPOINT=/hiddengem
```
</details>

### 💻 Running Locally

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fill in credentials
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
API base: `http://localhost:8000` · Swagger UI: `http://localhost:8000/docs`

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_BASE_URL
npm run dev
```
Client: `http://localhost:8080`

---

## 📥 Data Ingestion

The ingestion script fetches GitHub repositories, enriches each with full language lists and a cleaned README, generates a 384-dim embedding, and upserts into MongoDB.

```bash
cd backend
python ingest_repos.py
```

- Progress is checkpointed to `ingestion_state.json` — interrupted runs resume automatically.
- GitHub API rate limits are respected; the script pauses when limits are approached.
- After ingestion, create the required MongoDB indexes:

```bash
python scripts/create_indexes.py
```

Then create the **Atlas Vector Search index** manually in the Atlas UI:

1. Atlas → Cluster → **Atlas Search** → **Create Search Index** → **Atlas Vector Search** → **JSON Editor**
2. Use this definition and name the index `embedding_vector_index`:

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

---

## 🌐 API Overview

| Endpoint | Method | Description |
|---|:---:|---|
| `/` | `GET` | Health ping |
| `/health` | `GET` | DB connection check + repository count |
| `/search` | `POST` | Semantic search via Atlas Vector Search |
| `/userpreferences` | `POST` | Personalized recommendations from user profile |
| `/allrepos` | `GET` | Paginated catalog with filtering and sorting |
| `/hiddengem` | `GET` | Paginated hidden gems feed |
| `/repo/{owner}/{name}` | `GET` | Single repository detail with README |

---

## 🧪 Tests

```bash
# Backend — 99 tests
cd backend && pytest tests/ -v

# Frontend — 27 tests
cd frontend && npm test
```

---

## ☁️ Deployment

<details>
<summary><b>Backend (Railway, Render, Fly.io)</b></summary>

- Root directory: `backend/`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Inject `MONGO_URI`, `GEMINI_API_KEY`, and `ALLOWED_ORIGINS` as environment variables.
</details>

<details>
<summary><b>Frontend (Vercel, Netlify)</b></summary>

- Root directory: `frontend/`
- Build command: `npm run build`
- Output directory: `dist`
- Set `VITE_API_BASE_URL` to your production backend URL.
- `frontend/vercel.json` includes SPA rewrites — no extra configuration needed for Vercel.
</details>

---

## 🛡️ Production Considerations

- **CORS** — Restrict `ALLOWED_ORIGINS` to your exact frontend domain in production.
- **Secrets** — Store all API keys in your platform's secret manager, never in committed files.
- **Atlas Network Access** — Restrict MongoDB Atlas IP whitelist to your backend's egress IPs in production (avoid `0.0.0.0/0`).

<br />

---

<div align="center">
  <sub>Built by Team DOTENV</a></sub>
</div>
