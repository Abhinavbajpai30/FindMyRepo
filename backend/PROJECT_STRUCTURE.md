# 📁 Project Structure

Complete overview of the FindMyRepo backend architecture and file organization.

## Directory Structure

```
backend/
├── main.py                      # FastAPI application entry point
├── models.py                    # Pydantic models for request/response validation
├── database.py                  # MongoDB connection manager
├── requirements.txt             # Python package dependencies
├── README.md                    # Complete documentation
├── QUICKSTART.md               # Quick setup guide
├── .env.example                # Environment variables template
├── .env                        # Your environment variables (not in git)
├── test_api.py                 # API testing script
├── create_indexes.py           # MongoDB index creation utility
│
├── services/                   # Business logic layer
│   ├── search.py              # Search with vector similarity + Gemini queries
│   ├── recommendations.py     # Personalized recommendations engine
│   └── repository.py          # Repository filtering and pagination
│
└── utils/                      # Utility functions and helpers
    ├── gemini_service.py      # Google Gemini AI integration
    ├── embeddings.py          # Vector embedding generation
    └── helpers.py             # Data transformation utilities
```

## File Descriptions

### Core Application Files

#### `main.py` (343 lines)
**Purpose**: FastAPI application with all HTTP endpoints

**Key Components**:
- FastAPI app initialization with CORS
- Startup/shutdown event handlers
- 4 main endpoints: `/search`, `/userpreferences`, `/allrepos`, `/hiddengem`
- Health check and root endpoints
- Global exception handler

**Dependencies**: FastAPI, Pydantic models, all services

**Entry Point**: Run with `python main.py` or `uvicorn main:app`

---

#### `models.py` (90 lines)
**Purpose**: Pydantic models for request/response schemas

**Models**:
- `SearchRequest`: Search query input
- `UserPreferencesRequest`: User preference data
- `RepositoryResponse`: Standardized repo output format
- `SearchResponse`, `UserPreferencesResponse`: Search results
- `AllReposResponse`, `HiddenGemsResponse`: Paginated results
- `PaginationMetadata`: Pagination info
- `ErrorResponse`: Error format

**Why Pydantic?**: Automatic validation, serialization, API documentation

---

#### `database.py` (58 lines)
**Purpose**: MongoDB connection management

**Key Features**:
- Singleton pattern for database instance
- Connection pooling
- Error handling for connection failures
- Database and collection access methods

**Configuration**: Uses `MONGO_URI` from environment

---

### Services Layer

#### `services/search.py` (150 lines)
**Purpose**: Hybrid search combining Gemini queries + vector similarity

**How It Works**:
1. Generate query embedding using sentence-transformers
2. Use Gemini AI to create MongoDB filter from natural language
3. Query MongoDB to get candidate repositories
4. Calculate vector similarity for each candidate
5. Re-rank by similarity score
6. Return top results

**Key Methods**:
- `search(query, limit)`: Main search function
- `search_with_filters()`: Direct filtering (used by `/allrepos`)

---

#### `services/recommendations.py` (130 lines)
**Purpose**: Personalized repository recommendations

**Algorithm**:
1. Use Gemini to map user preferences to MongoDB query
2. Apply domain-to-topic mapping
3. Filter by preferred languages
4. Adjust star range based on expertise level
5. Calculate preference matching score
6. Rank by combined score

**Scoring Components** (weights):
- Language match: 40%
- Domain/topic match: 30%
- Popularity: 20%
- Recency: 10%

---

#### `services/repository.py` (165 lines)
**Purpose**: Repository listing with advanced filtering

**Endpoints Served**:
- `/allrepos`: All repositories with comprehensive filters
- `/hiddengem`: Curated low-star, high-quality repos

**Filter Support**:
- Languages, topics
- Star range, fork range
- Name/description search
- Boolean flags (hacktoberfest, GSOC, underrated)

**Hidden Gems Criteria**:
- 100-1000 stars
- Updated within 18 months
- Non-empty README
- At least 1 open issue

---

### Utilities

#### `utils/gemini_service.py` (220 lines)
**Purpose**: Google Gemini AI integration for query generation

**Key Features**:
- Converts natural language to MongoDB queries
- Domain-to-topic mapping for preferences
- Expertise-level to star-range mapping
- Handles JSON parsing and error recovery

**Prompts**:
- Search prompt: Analyzes query for languages, topics, keywords
- Preference prompt: Maps user profile to repository filters

**Error Handling**: Falls back to basic queries if Gemini fails

---

#### `utils/embeddings.py` (60 lines)
**Purpose**: Vector embedding generation and similarity calculation

**Model**: `all-MiniLM-L6-v2` (384 dimensions)
- Same model as ingestion script for consistency
- Loaded once at startup
- Cached in memory for performance

**Methods**:
- `generate(text)`: Create embedding for query
- `calculate_similarity()`: Cosine similarity between vectors

---

#### `utils/helpers.py` (80 lines)
**Purpose**: Data transformation and utility functions

**Functions**:
- `transform_repo_to_response()`: MongoDB doc → API response
- `transform_repos_list()`: Batch transformation
- `calculate_pagination_metadata()`: Generate pagination info

**Why Separate?**: Keeps business logic clean, reusable transformations

---

### Configuration & Setup

#### `requirements.txt` (9 packages)
```
fastapi==0.104.1              # Web framework
uvicorn[standard]==0.24.0     # ASGI server
pymongo==4.6.0                # MongoDB driver
sentence-transformers==2.2.2   # Embeddings
google-generativeai==0.3.2    # Gemini AI
python-dotenv==1.0.0          # Environment variables
pydantic==2.5.0               # Data validation
numpy==1.24.3                 # Array operations
scipy==1.11.4                 # Scientific computing
```

#### `.env.example` / `.env`
Environment configuration template and actual values

**Required Variables**:
- `MONGO_URI`: MongoDB connection string
- `GEMINI_API_KEY`: Google Gemini API key
- `HOST`, `PORT`: Server configuration
- `ALLOWED_ORIGINS`: CORS whitelist

---

### Testing & Utilities

#### `test_api.py` (250 lines)
**Purpose**: Comprehensive API testing script

**Tests**:
1. Health check
2. Search with multiple queries
3. User preferences with sample data
4. All repos with various filters
5. Hidden gems endpoint

**Usage**: `python test_api.py` (after starting server)

---

#### `create_indexes.py` (200 lines)
**Purpose**: Automated MongoDB index creation

**Creates**:
- Compound indexes for sorting
- Single-field indexes for filtering
- Unique index on `github_id`
- Specialized index for hidden gems

**Usage**: `python create_indexes.py`

**Note**: Vector search index must be created manually in Atlas

---

## Data Flow

### Search Request Flow
```
User Query
    ↓
FastAPI Endpoint (/search)
    ↓
SearchService.search()
    ├─→ EmbeddingGenerator (create query embedding)
    ├─→ GeminiService (generate MongoDB filter)
    ├─→ MongoDB (query with filter)
    ├─→ Calculate similarity scores
    └─→ Re-rank by similarity
    ↓
Transform to API response
    ↓
Return to user
```

### User Preferences Flow
```
User Preferences (domains, languages, expertise)
    ↓
FastAPI Endpoint (/userpreferences)
    ↓
RecommendationService.get_personalized_repos()
    ├─→ GeminiService (map preferences to query)
    ├─→ MongoDB (filter by generated query)
    ├─→ Calculate preference scores
    └─→ Rank by scores
    ↓
Transform to API response
    ↓
Return to user
```

### All Repos / Hidden Gems Flow
```
Query Parameters (page, limit, filters, sort)
    ↓
FastAPI Endpoint (/allrepos or /hiddengem)
    ↓
RepositoryService
    ├─→ Build MongoDB filter
    ├─→ Calculate pagination (skip, limit)
    ├─→ Query MongoDB
    └─→ Get total count
    ↓
Transform results + generate pagination metadata
    ↓
Return to user
```

## Architecture Principles

### Separation of Concerns
- **Routes** (main.py): HTTP handling only
- **Services**: Business logic
- **Utils**: Reusable functions
- **Models**: Data validation

### Error Handling
- Try-catch blocks in all service methods
- Logging at each layer
- Graceful fallbacks (e.g., basic search if Gemini fails)
- Meaningful error messages to users

### Performance Optimizations
1. **Caching**: Embedding model loaded once at startup
2. **Indexing**: MongoDB indexes for fast queries
3. **Pagination**: Limit data transfer
4. **Projection**: Exclude large fields (embedding, readme) from responses
5. **Connection Pooling**: MongoDB client handles automatically

### Scalability Considerations
- Stateless design (no session storage)
- Horizontal scaling possible (multiple uvicorn workers)
- Database connection pooling
- Async-ready (can add async/await later)

## Development Workflow

### Adding a New Endpoint

1. **Define Models** (`models.py`):
   ```python
   class NewRequest(BaseModel):
       field: str
   
   class NewResponse(BaseModel):
       success: bool
       data: List[Dict]
   ```

2. **Create Service** (`services/new_service.py`):
   ```python
   class NewService:
       def __init__(self, collection):
           self.collection = collection
       
       def process(self, params):
           # Business logic here
           pass
   ```

3. **Add Endpoint** (`main.py`):
   ```python
   @app.post("/new-endpoint", response_model=NewResponse)
   async def new_endpoint(request: NewRequest):
       results = new_service.process(request)
       return NewResponse(success=True, data=results)
   ```

4. **Add Test** (`test_api.py`):
   ```python
   def test_new_endpoint():
       response = requests.post(f"{BASE_URL}/new-endpoint", json=data)
       assert response.status_code == 200
   ```

### Code Style
- Type hints for function parameters and returns
- Docstrings for classes and public methods
- Logging at info/error levels
- Pydantic for all external-facing data
- Error handling with try-except-log-raise pattern

## Security Features

1. **Environment Variables**: Sensitive data not hardcoded
2. **CORS**: Restricted to allowed origins
3. **Input Validation**: Pydantic validates all inputs
4. **Error Messages**: Don't leak internal details
5. **Connection Security**: MongoDB uses TLS

## Future Enhancements

Potential additions:
- [ ] Rate limiting
- [ ] API key authentication
- [ ] Response caching (Redis)
- [ ] Async database operations
- [ ] GraphQL endpoint
- [ ] WebSocket for real-time updates
- [ ] More sophisticated ranking algorithms
- [ ] A/B testing framework
- [ ] Analytics and metrics collection

## Contributing Guidelines

1. Follow existing code structure
2. Add tests for new features
3. Update documentation
4. Use type hints
5. Handle errors gracefully
6. Log important operations

---

This structure is designed for maintainability, testability, and scalability. Each component has a single responsibility, making it easy to understand, modify, and extend.