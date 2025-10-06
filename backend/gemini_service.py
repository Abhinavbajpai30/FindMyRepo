import google.genai as genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = "gemini-2.0-flash"
        
    def generate_weaviate_code(self, user_query: str) -> str:
        """Convert natural language query to Weaviate Python code"""
        
        prompt = """You are a Weaviate query code generator expert. Your job is to convert natural language queries into executable Python code using the Weaviate v4 client.

# Available Schema
Collection Name: "Repos"

Properties:
- repo_id (INT) - Repository ID
- name (TEXT) - Repository name
- full_name (TEXT) - Full repository name (owner/repo)
- owner (TEXT) - Repository owner
- url (TEXT) - GitHub URL
- homepage (TEXT)
- description (TEXT) - Repository description
- readme (TEXT) - README content (truncated)
- language (TEXT) - Primary programming language (lowercase)
- languages (TEXT) - Comma-separated list of languages (lowercase)
- topics (TEXT) - Comma-separated list of topics (comma-separated string)
- stars (INT) - Number of stars
- forks (INT) - Number of forks
- open_issues (INT)
- created_at (TEXT)
- updated_at (TEXT)
- license (TEXT)
- has_issues (BOOL)
- has_wiki (BOOL)
- default_branch (TEXT) - Default branch name
- is_gsoc (BOOL) - Google Summer of Code participant
- is_hacktoberfest (BOOL) - Hacktoberfest participant
- is_underrated (BOOL) - Underrated project flag
- has_good_first_issues (BOOL) - Has good first issues for beginners
- sources (TEXT) - Comma-separated list of sources
- combined_text (TEXT) - Combined searchable text

# Available Query Types

1. **Semantic/Vector Search** - Use for natural language queries about concepts, features, or descriptions
   ```python
   collection.query.near_vector(
       near_vector=query_vector,
       limit=10,
       return_properties=[...],
       filters=...  # optional
   )
   ```

2. **Keyword/Metadata Search** - Use ONLY when filtering by exact metadata (stars, forks, dates)
   ```python
   collection.query.fetch_objects(
       filters=...,
       limit=10,
       return_properties=[...]
   )
   ```

3. **Hybrid Search** - Combine semantic + keyword (BEST for most queries with filters)
   ```python
   collection.query.hybrid(
       query=query_text,
       vector=query_vector,
       alpha=0.7,  # 0=keyword only, 1=vector only, 0.7=prefer semantic
       limit=10,
       filters=...
   )
   ```

# Filter Operations

```python
from weaviate.classes.query import Filter

# Comparison
Filter.by_property("stars").greater_than(100)
Filter.by_property("stars").greater_or_equal(100)
Filter.by_property("stars").less_than(1000)
Filter.by_property("stars").less_or_equal(1000)
Filter.by_property("language").equal("python")

# Array/List operations (for topics, languages fields)
Filter.by_property("topics").contains_any(["ci-cd", "pipeline"])  # Match ANY of these
Filter.by_property("topics").contains_all(["ci", "docker"])       # Match ALL of these
Filter.by_property("topics").contains_none(["deprecated"])        # Match NONE of these

# String pattern matching (case-insensitive by default)
Filter.by_property("name").like("*jenkins*")
Filter.by_property("description").like("*continuous integration*")

# Logical operators
filter1 & filter2  # AND
filter1 | filter2  # OR
```

# CRITICAL: Open Source Project Filtering

When users request "open source repos only" or "legitimate projects", you MUST apply these base filters:

```python
# MANDATORY Open Source Base Filters
opensource_filters = (
    Filter.by_property("stars").greater_or_equal(10) &
    Filter.by_property("forks").greater_or_equal(3) &
    Filter.by_property("has_issues").equal(True)
)
```

**Why these filters matter:**
- `stars >= 10`: Real projects have community interest (filters out personal demos)
- `forks >= 3`: Active projects get forked (shows reuse and legitimacy)
- `has_issues = true`: Legitimate open source projects enable issue tracking

**Exclude tutorial/demo patterns in name:**
Use `contains_none()` or manual exclusions for topics containing:
- "tutorial", "learning", "demo", "example", "sample", "practice", "homework", "assignment", "boilerplate", "template", "starter"

# CRITICAL: Topic/Keyword Extraction Rules

When the user mentions specific technologies, tools, or concepts, you MUST:
1. **Extract relevant keywords and topics** from the user's query
2. **Apply filters using contains_any()** on the "topics" field
3. **Use semantic search** to find conceptually similar repos
4. **Combine filters intelligently** - don't just do pure vector search
5. **Add open source filters** when user mentions "open source only" or "legitimate projects"

Common topic patterns to recognize:
- **Frontend Developer** → languages: ["javascript", "typescript", "html", "css"], topics: ["frontend", "web", "ui", "react", "vue", "angular", "svelte"]
- **Backend Developer** → languages: ["python", "java", "go", "rust", "nodejs"], topics: ["backend", "api", "server", "database", "microservices"]
- **CI/CD** → topics: ["ci-cd", "ci", "cd", "continuous-integration", "continuous-deployment", "continuous-delivery"]
- **Pipelines** → topics: ["pipeline", "pipelines", "workflow", "automation"]
- **Docker** → topics: ["docker", "container", "containerization"]
- **Kubernetes** → topics: ["kubernetes", "k8s", "orchestration"]
- **Machine Learning** → topics: ["machine-learning", "ml", "ai", "deep-learning"]
- **Data Science** → topics: ["data-science", "data-analysis", "data-visualization", "analytics"]
- **DevOps** → topics: ["devops", "infrastructure", "automation", "deployment"]

# Important Rules

1. ALWAYS import required classes at the top
2. Assume these variables exist:
   - `client` - Weaviate client instance (NOT weaviate_client)
   - `model` - SentenceTransformer model for embeddings
   - `query_text` - The user's search query as a string
3. **ALWAYS generate query_vector** for semantic/vector/hybrid search
4. **ALWAYS add topic filters** when user mentions specific technologies or domains
5. **ALWAYS add open source base filters** when user mentions "open source only" or "legitimate"
6. Return ALL relevant properties: ["name", "full_name", "description", "readme", "topics", "stars", "forks", "open_issues", "license", "has_issues", "has_wiki", "url", "language", "languages"]
7. Set reasonable limits:
   - Default: 20 (to allow post-filtering)
   - If user wants "suggestions" or "many": 30
   - If user wants "top" or "best": 15
8. For language filters, convert to lowercase
9. **Prefer hybrid search over pure vector search** when you have filters
10. When user asks for "repos about X" or "interested in X", extract topics from X
11. **ALWAYS filter has_issues=true**

# Output Format

Provide ONLY the Python code that executes the query. 
DO NOT include:
- Explanations or comments
- Markdown code blocks (no ```python or ```)
- Extra text before or after the code
- Any formatting markers

The output must be raw, executable Python code that can be run directly with exec().

The code should:
1. Import necessary classes (if filters are used)
2. Get the collection
3. Generate embeddings (query_vector)
4. Build filters based on extracted topics/keywords
5. Add open source filters if requested
6. Execute the query (prefer hybrid or near_vector with filters)
7. Store results in a variable called `results`

# Examples

User Query: "Find popular Python machine learning libraries"
Output:
from weaviate.classes.query import Filter

collection = client.collections.get("Repos")
query_vector = model.encode([query_text])[0].tolist()

filters = (
    Filter.by_property("languages").contains_any(["python"]) &
    Filter.by_property("topics").contains_any(["machine-learning", "ml", "ai", "deep-learning"]) &
    Filter.by_property("stars").greater_or_equal(500)
)

results = collection.query.near_vector(
    near_vector=query_vector,
    filters=filters,
    limit=20,
    return_properties=["name", "full_name", "owner", "description", "readme", "topics", "stars", "forks", "open_issues", "license", "has_issues", "has_wiki", "url", "language", "languages", "repo_id", "homepage", "created_at", "updated_at", "default_branch", "is_gsoc", "is_hacktoberfest", "is_underrated", "has_good_first_issues", "sources", "combined_text"]
)

User Query: "Show me JavaScript repos with more than 1000 stars"
Output:
from weaviate.classes.query import Filter

collection = client.collections.get("Repos")
query_vector = model.encode([query_text])[0].tolist()

filters = (
    Filter.by_property("languages").contains_any(["javascript"]) &
    Filter.by_property("stars").greater_than(1000)
)

results = collection.query.near_vector(
    near_vector=query_vector,
    filters=filters,
    limit=20,
    return_properties=["name", "full_name", "owner", "description", "readme", "topics", "stars", "forks", "open_issues", "license", "has_issues", "has_wiki", "url", "language", "languages", "repo_id", "homepage", "created_at", "updated_at", "default_branch", "is_gsoc", "is_hacktoberfest", "is_underrated", "has_good_first_issues", "sources", "combined_text"]
)

User Query: "Find web frameworks in Python or JavaScript"
Output:
from weaviate.classes.query import Filter

collection = client.collections.get("Repos")
query_vector = model.encode([query_text])[0].tolist()

filters = (
    (Filter.by_property("languages").contains_any(["python"]) | 
     Filter.by_property("languages").contains_any(["javascript"])) &
    Filter.by_property("topics").contains_any(["web", "framework", "webapp", "api"])
)

results = collection.query.near_vector(
    near_vector=query_vector,
    filters=filters,
    limit=20,
    return_properties=["name", "full_name", "description", "readme", "topics", "stars", "forks", "open_issues", "license", "has_issues", "has_wiki", "url", "language", "languages"]
)

User Query: "I'm interested in CI/CD and pipelines, suggest open source repos"
Output:
from weaviate.classes.query import Filter

collection = client.collections.get("Repos")
query_vector = model.encode([query_text])[0].tolist()

filters = (
    Filter.by_property("topics").contains_any([
        "ci-cd", "ci", "cd", "continuous-integration", "continuous-deployment",
        "pipeline", "pipelines", "workflow", "automation", "devops"
    ]) &
    Filter.by_property("stars").greater_or_equal(10) &
    Filter.by_property("forks").greater_or_equal(3) &
    Filter.by_property("has_issues").equal(True)
)

results = collection.query.near_vector(
    near_vector=query_vector,
    filters=filters,
    limit=20,
    return_properties=["name", "full_name", "description", "readme", "topics", "stars", "forks", "open_issues", "license", "has_issues", "has_wiki", "url", "language", "languages"]
)

User Query: "I am a frontend developer, open source repos only"
Output:
from weaviate.classes.query import Filter

collection = client.collections.get("Repos")
query_vector = model.encode([query_text])[0].tolist()

filters = (
    Filter.by_property("languages").contains_any(["javascript", "typescript", "html", "css"]) &
    Filter.by_property("topics").contains_any(["frontend", "web", "ui", "react", "vue", "angular", "svelte", "webapp"]) &
    Filter.by_property("stars").greater_or_equal(10) &
    Filter.by_property("forks").greater_or_equal(3) &
    Filter.by_property("has_issues").equal(True)
)

results = collection.query.near_vector(
    near_vector=query_vector,
    filters=filters,
    limit=20,
    return_properties=["name", "full_name", "description", "readme", "topics", "stars", "forks", "open_issues", "license", "has_issues", "has_wiki", "url", "language", "languages"]
)

User Query: "Backend Python frameworks for APIs, only legitimate projects"
Output:
from weaviate.classes.query import Filter

collection = client.collections.get("Repos")
query_vector = model.encode([query_text])[0].tolist()

filters = (
    Filter.by_property("languages").contains_any(["python"]) &
    Filter.by_property("topics").contains_any(["backend", "api", "framework", "web", "rest", "graphql"]) &
    Filter.by_property("stars").greater_or_equal(10) &
    Filter.by_property("forks").greater_or_equal(3) &
    Filter.by_property("has_issues").equal(True)
)

results = collection.query.near_vector(
    near_vector=query_vector,
    filters=filters,
    limit=20,
    return_properties=["name", "full_name", "description", "readme", "topics", "stars", "forks", "open_issues", "license", "has_issues", "has_wiki", "url", "language", "languages"]
)

User Query: "Docker and Kubernetes repos with good documentation"
Output:
from weaviate.classes.query import Filter

collection = client.collections.get("Repos")
query_vector = model.encode([query_text])[0].tolist()

filters = (
    Filter.by_property("topics").contains_any([
        "docker", "kubernetes", "k8s", "container", "orchestration", "containerization"
    ]) &
    Filter.by_property("has_wiki").equal(True)
)

results = collection.query.near_vector(
    near_vector=query_vector,
    filters=filters,
    limit=20,
    return_properties=["name", "full_name", "description", "readme", "topics", "stars", "forks", "open_issues", "license", "has_issues", "has_wiki", "url", "language", "languages"]
)

# CRITICAL REMINDERS
1. When users mention specific domains, technologies, or interests:
   - Extract the key topics/keywords
   - Add them to a contains_any() filter on "topics"
   - Use semantic search (near_vector) to find conceptually similar repos
   - DO NOT rely only on vector similarity without filters

2. **MANDATORY: ALWAYS return ALL properties in EVERY query:**
   return_properties=["name", "full_name", "owner", "description", "readme", "topics", "stars", "forks", "open_issues", "license", "has_issues", "has_wiki", "url", "language", "languages", "repo_id", "homepage", "created_at", "updated_at", "default_branch", "is_gsoc", "is_hacktoberfest", "is_underrated", "has_good_first_issues", "sources", "combined_text"]
   
   This is NON-NEGOTIABLE. Every single query must return all properties for downstream processing.

3. When users request "open source only" or "legitimate projects":
   - ALWAYS add: stars >= 10, forks >= 3, has_issues = true
   - These filters ensure quality, community-driven projects

4. Set limit to 20-30 for queries that need post-filtering (open source, legitimate projects)

Now convert the user's query into executable Weaviate Python code:

User Query: """ + f'"{user_query}"'
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2)
        )
        
        generated_code = response.text.strip()

        if generated_code.startswith("```python"):
            generated_code = generated_code[9:]
        elif generated_code.startswith("```"):
            generated_code = generated_code[3:]

        if generated_code.endswith("```"):
            generated_code = generated_code[:-3]

        generated_code = generated_code.strip()

        return generated_code