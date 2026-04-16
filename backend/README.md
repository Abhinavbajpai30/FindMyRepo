# FindMyRepo Backend API

FastAPI backend for the FindMyRepo GitHub repository discovery platform. This API provides intelligent search, personalized recommendations, and advanced filtering capabilities using AI-powered query generation.

## 🚀 Features

- **Intelligent Search**: Natural language search powered by Gemini AI and vector embeddings
- **Personalized Recommendations**: Get repository suggestions based on your interests and expertise
- **Advanced Filtering**: Filter repositories by language, topics, stars, and more
- **Hidden Gems Discovery**: Find high-quality repositories with < 1000 stars
- **Pagination & Sorting**: Efficient data retrieval with flexible sorting options

## 📋 Prerequisites

- Python 3.9+
- MongoDB Atlas account (with vector search capability)
- Google Gemini API key
- MongoDB database with repositories collection (from ingestion script)

## 🛠️ Installation

1. **Clone the repository**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
GEMINI_API_KEY=your_gemini_api_key_here
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

## 📊 MongoDB Atlas Vector Search Setup

For optimal performance, you need to create indexes in MongoDB Atlas.

### 1. Vector Search Index (for semantic search)

Go to MongoDB Atlas → Your Cluster → Search → Create Search Index

**Index Name**: `vector_index`

**Index Definition**:
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

### 2. Standard Indexes (for filtering and sorting)

Run these commands in MongoDB Shell or Compass:

```javascript
// Switch to your database
use findmyrepo

// Create compound index for common queries
db.repos.createIndex({ "stars": -1, "pushed_at": -1 })

// Create index for language filtering
db.repos.createIndex({ "languages": 1 })

// Create index for topic filtering
db.repos.createIndex({ "topics": 1 })

// Create index for name search
db.repos.createIndex({ "name": "text", "description": "text" })

// Create index for pushed_at (date filtering)
db.repos.createIndex({ "pushed_at": -1 })

// Create compound index for hidden gems query
db.repos.createIndex({ "stars": 1, "pushed_at": -1, "readme": 1 })

// Create index on github_id for uniqueness
db.repos.createIndex({ "github_id": 1 }, { unique: true })
```

### Verify Indexes

```javascript
// List all indexes
db.repos.getIndexes()
```

## 🏃 Running the Server

### Development Mode

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 API Endpoints

### 1. Search Repositories
```http
POST /search
Content-Type: application/json

{
  "query": "python machine learning framework"
}
```

### 2. Personalized Recommendations
```http
POST /userpreferences
Content-Type: application/json

{
  "primaryDomains": ["ML / AI / Data Science", "Backend / APIs"],
  "role": "Software Developer / Engineer",
  "expertise": "Medium",
  "preferredLanguages": ["Python", "JavaScript"]
}
```

### 3. All Repositories (with filters)
```http
GET /allrepos?page=1&limit=20&sort_by=stars&sort_order=desc&languages=Python,JavaScript&min_stars=100
```

### 4. Hidden Gems
```http
GET /hiddengem?page=1&limit=20&sort_by=stars&sort_order=desc
```

### 5. Health Check
```http
GET /health
```

## 🧠 How It Works

### Search Flow
1. User sends natural language query
2. Backend generates embedding vector using sentence-transformers
3. Gemini AI generates MongoDB filter query from the natural language
4. MongoDB query finds candidate repositories
5. Vector similarity ranking refines results
6. Top results returned to user

### Personalized Recommendations Flow
1. User submits preferences (domains, languages, expertise)
2. Gemini AI maps preferences to MongoDB query
3. Additional scoring based on preference matching
4. Results ranked by relevance score

### Architecture
```
┌─────────────┐
│   Client    │
│  (Frontend) │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         FastAPI Backend             │
│  ┌───────────┐  ┌────────────────┐ │
│  │  Gemini   │  │  Embeddings    │ │
│  │  Service  │  │  Generator     │ │
│  └───────────┘  └────────────────┘ │
│         │              │            │
│         ▼              ▼            │
│  ┌──────────────────────────────┐  │
│  │    Search/Recommendation     │  │
│  │         Services             │  │
│  └──────────────┬───────────────┘  │
└─────────────────┼───────────────────┘
                  │
                  ▼
          ┌───────────────┐
          │   MongoDB     │
          │   Atlas       │
          └───────────────┘
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_URI` | MongoDB connection string | Required |
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | `http://localhost:5173` |

### Gemini AI Prompts

The system uses carefully crafted prompts to generate MongoDB queries. Key features:
- Domain-to-topic mapping for user preferences
- Expertise-level to star-range mapping
- Language filtering
- Recency filtering for active projects

## 🐛 Debugging

### Enable Debug Logging
```python
# In main.py, change logging level
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

**Issue**: "GEMINI_API_KEY not found"
- **Solution**: Ensure `.env` file exists and contains valid API key

**Issue**: "Failed to connect to MongoDB"
- **Solution**: Check MONGO_URI format and network access in MongoDB Atlas

**Issue**: Vector search not working
- **Solution**: Verify vector search index is created in MongoDB Atlas

**Issue**: Search returns no results
- **Solution**: Check that repositories have embeddings in the database

## 📈 Performance Optimization

1. **Caching**: The sentence-transformers model is loaded once at startup
2. **Indexing**: MongoDB indexes speed up queries significantly
3. **Pagination**: Limits database load by fetching only needed data
4. **Connection Pooling**: MongoDB client handles connection pooling automatically

## 🧪 Testing

### Manual Testing with curl

```bash
# Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "web framework python"}'

# User Preferences
curl -X POST http://localhost:8000/userpreferences \
  -H "Content-Type: application/json" \
  -d '{
    "primaryDomains": ["Backend / APIs"],
    "role": "Software Developer / Engineer",
    "expertise": "Medium",
    "preferredLanguages": ["Python"]
  }'

# All Repos
curl "http://localhost:8000/allrepos?page=1&limit=10&sort_by=stars&sort_order=desc"

# Hidden Gems
curl "http://localhost:8000/hiddengem?page=1&limit=10"
```

## 📝 Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── models.py              # Pydantic models (request/response schemas)
├── database.py            # MongoDB connection manager
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Environment variables (not in git)
├── services/
│   ├── search.py         # Search logic with vector similarity
│   ├── recommendations.py # Personalized recommendations
│   └── repository.py     # Repository filtering and pagination
└── utils/
    ├── gemini_service.py # Gemini AI query generation
    ├── embeddings.py     # Embedding generation
    └── helpers.py        # Data transformation utilities
```

## 🤝 Integration with Frontend

The backend is designed to work seamlessly with the provided frontend. Set these environment variables in your frontend `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SEARCH_API_URL=http://localhost:8000/search
VITE_ALL_REPOS_ENDPOINT=/allrepos
VITE_HIDDEN_GEMS_ENDPOINT=/hiddengem
VITE_USER_PREFERENCES_API=http://localhost:8000/userpreferences
```

## 🔐 Security Considerations

- API keys stored in environment variables
- CORS configured to allow only specified origins
- Input validation using Pydantic models
- Error handling prevents information leakage

## 📄 License

This project is part of the FindMyRepo platform.

## 🙏 Acknowledgments

- Google Gemini AI for intelligent query generation
- sentence-transformers for semantic embeddings
- FastAPI for the excellent web framework
- MongoDB Atlas for vector search capabilities