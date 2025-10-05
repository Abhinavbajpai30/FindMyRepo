from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import math

from gemini_service import GeminiService
from weaviate_service import WeaviateService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FindMyRepo API",
    description="Natural language search for GitHub repositories using Gemini AI and Weaviate",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Repository(BaseModel):
    name: str = ""
    full_name: str = ""
    description: str = ""
    url: str = ""
    homepage: Optional[str] = ""
    language: str = ""
    languages: List[str] = []
    topics: List[str] = []
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    license: Optional[str] = ""
    has_issues: bool = False
    has_wiki: bool = False
    created_at: str = ""
    updated_at: str = ""
    distance: Optional[float] = None
    score: Optional[float] = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language search query")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Maximum number of results to return")


class SearchResponse(BaseModel):
    success: bool
    query: str
    results_count: int
    results: List[Repository]
    error: Optional[str] = None
    generated_code: Optional[str] = None

class PaginationRequest(BaseModel):
    page: int = Field(1, ge=1, description="Page number (starts from 1)")
    limit: int = Field(20, ge=1, le=100, description="Number of items per page (max 100)")
    sort_by: str = Field("stars", description="Sort by field (stars, forks, updated_at, created_at, name)")
    sort_order: str = Field("desc", description="Sort order (asc or desc)")

class PaginatedResponse(BaseModel):
    success: bool
    data: List[Repository]
    pagination: Dict[str, Any]
    filters_applied: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class RepositoryFilters(BaseModel):
    """Filters for repository queries"""
    language: Optional[str] = Field(None, description="Filter by primary programming language (case insensitive)")
    languages: Optional[List[str]] = Field(None, description="Filter by any of these languages")
    topics: Optional[List[str]] = Field(None, description="Filter by any of these topics")
    min_stars: Optional[int] = Field(None, ge=0, description="Minimum number of stars")
    max_stars: Optional[int] = Field(None, ge=0, description="Maximum number of stars")
    min_forks: Optional[int] = Field(None, ge=0, description="Minimum number of forks")
    max_forks: Optional[int] = Field(None, ge=0, description="Maximum number of forks")
    license: Optional[str] = Field(None, description="Filter by license type")
    has_issues: Optional[bool] = Field(None, description="Filter repositories with/without issues enabled")
    has_wiki: Optional[bool] = Field(None, description="Filter repositories with/without wiki enabled")
    is_underrated: Optional[bool] = Field(None, description="Filter underrated repositories")
    is_gsoc: Optional[bool] = Field(None, description="Filter Google Summer of Code repositories")
    is_hacktoberfest: Optional[bool] = Field(None, description="Filter Hacktoberfest repositories")
    has_good_first_issues: Optional[bool] = Field(None, description="Filter repositories with good first issues")
    name_contains: Optional[str] = Field(None, description="Filter repositories where name contains this text")
    description_contains: Optional[str] = Field(None, description="Filter repositories where description contains this text")

# Global service instances (in production, consider using dependency injection)
gemini_service = GeminiService()
weaviate_service = WeaviateService()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "FindMyRepo API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "gemini": "connected",
            "weaviate": "connected"
        }
    }

@app.post("/search", response_model=SearchResponse)
async def search_repositories(request: SearchRequest):
    """
    Search for repositories using natural language queries.
    
    The process:
    1. Takes a natural language query from the user
    2. Uses Gemini AI to convert it to Weaviate Python code
    3. Executes the generated code against the Weaviate database
    4. Returns formatted results as JSON
    
    Examples:
    - "Find popular Python machine learning libraries"
    - "JavaScript frameworks with more than 1000 stars"
    - "Docker and Kubernetes repositories"
    - "CI/CD tools and pipelines"
    """
    try:
        logger.info(f"Processing search query: {request.query}")
        
        # Step 1: Generate Weaviate code using Gemini
        try:
            generated_code = gemini_service.generate_weaviate_code(request.query)
            logger.info(f"Generated code: {generated_code[:200]}...")
        except Exception as e:
            logger.error(f"Gemini service error: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate search code: {str(e)}"
            )
        
        # Step 2: Execute search using Weaviate
        try:
            search_results = weaviate_service.search(request.query, generated_code)
            logger.info(f"Search completed. Found {search_results.get('results_count', 0)} results")
        except Exception as e:
            logger.error(f"Weaviate service error: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to execute search: {str(e)}"
            )
        
        # Step 3: Format and return response
        if not search_results.get('success', False):
            return SearchResponse(
                success=False,
                query=request.query,
                results_count=0,
                results=[],
                error=search_results.get('error', 'Unknown error occurred'),
                generated_code=search_results.get('generated_code')
            )
        
        # Apply limit if specified
        results = search_results.get('results', [])
        if request.limit and len(results) > request.limit:
            results = results[:request.limit]
        
        # Convert to Repository models
        repositories = [Repository(**repo) for repo in results]
        
        return SearchResponse(
            success=True,
            query=request.query,
            results_count=len(repositories),
            results=repositories,
            generated_code=search_results.get('generated_code')
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in search endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/allrepos", response_model=PaginatedResponse)
async def get_all_repositories(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page (max 100)"),
    sort_by: str = Query("stars", description="Sort by field (stars, forks, updated_at, created_at, name)"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    # Filter parameters
    language: Optional[str] = Query(None, description="Filter by primary programming language"),
    languages: Optional[str] = Query(None, description="Filter by languages (comma-separated)"),
    topics: Optional[str] = Query(None, description="Filter by topics (comma-separated)"),
    min_stars: Optional[int] = Query(None, ge=0, description="Minimum number of stars"),
    max_stars: Optional[int] = Query(None, ge=0, description="Maximum number of stars"),
    min_forks: Optional[int] = Query(None, ge=0, description="Minimum number of forks"),
    max_forks: Optional[int] = Query(None, ge=0, description="Maximum number of forks"),
    license: Optional[str] = Query(None, description="Filter by license type"),
    has_issues: Optional[bool] = Query(None, description="Filter repositories with/without issues enabled"),
    has_wiki: Optional[bool] = Query(None, description="Filter repositories with/without wiki enabled"),
    is_underrated: Optional[bool] = Query(None, description="Filter underrated repositories"),
    is_gsoc: Optional[bool] = Query(None, description="Filter Google Summer of Code repositories"),
    is_hacktoberfest: Optional[bool] = Query(None, description="Filter Hacktoberfest repositories"),
    has_good_first_issues: Optional[bool] = Query(None, description="Filter repositories with good first issues"),
    name_contains: Optional[str] = Query(None, description="Filter repositories where name contains this text"),
    description_contains: Optional[str] = Query(None, description="Filter repositories where description contains this text")
):
    """
    Get all repositories with comprehensive filtering, pagination and sorting.
    
    This endpoint supports extensive filtering options to help you find specific types of repositories.
    All text filters are case-insensitive. Multiple values can be provided for languages and topics
    using comma-separated strings.
    
    Examples:
    - `/allrepos?language=python&min_stars=1000` - Python repos with 1000+ stars
    - `/allrepos?topics=machine-learning,ai&has_wiki=true` - ML repos with wikis
    - `/allrepos?languages=python,javascript&is_underrated=true` - Underrated Python/JS repos
    - `/allrepos?name_contains=framework&min_forks=100` - Framework repos with 100+ forks
    """
    try:
        # Validate parameters
        if sort_by not in ["stars", "forks", "updated_at", "created_at", "name"]:
            raise HTTPException(status_code=400, detail="Invalid sort_by field")
        if sort_order not in ["asc", "desc"]:
            raise HTTPException(status_code=400, detail="Sort order must be 'asc' or 'desc'")
        
        # Parse comma-separated values
        languages_list = [lang.strip().lower() for lang in languages.split(',')] if languages else None
        topics_list = [topic.strip().lower() for topic in topics.split(',')] if topics else None
        
        # Build filters applied info for response
        filters_applied = {}
        if language:
            filters_applied['language'] = language.lower()
        if languages_list:
            filters_applied['languages'] = languages_list
        if topics_list:
            filters_applied['topics'] = topics_list
        if min_stars is not None:
            filters_applied['min_stars'] = min_stars
        if max_stars is not None:
            filters_applied['max_stars'] = max_stars
        if min_forks is not None:
            filters_applied['min_forks'] = min_forks
        if max_forks is not None:
            filters_applied['max_forks'] = max_forks
        if license:
            filters_applied['license'] = license
        if has_issues is not None:
            filters_applied['has_issues'] = has_issues
        if has_wiki is not None:
            filters_applied['has_wiki'] = has_wiki
        if is_underrated is not None:
            filters_applied['is_underrated'] = is_underrated
        if is_gsoc is not None:
            filters_applied['is_gsoc'] = is_gsoc
        if is_hacktoberfest is not None:
            filters_applied['is_hacktoberfest'] = is_hacktoberfest
        if has_good_first_issues is not None:
            filters_applied['has_good_first_issues'] = has_good_first_issues
        if name_contains:
            filters_applied['name_contains'] = name_contains
        if description_contains:
            filters_applied['description_contains'] = description_contains
        
        logger.info(f"Fetching repositories: page={page}, limit={limit}, sort_by={sort_by}, sort_order={sort_order}, filters={filters_applied}")
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get collection and import Filter
        collection = weaviate_service.client.collections.get("Repos")
        from weaviate.classes.query import Filter, Sort
        
        # Build filter conditions
        filter_conditions = []
        
        # Language filters
        if language:
            filter_conditions.append(Filter.by_property("language").equal(language.lower()))
        
        if languages_list:
            filter_conditions.append(Filter.by_property("languages").contains_any(languages_list))
        
        # Topic filters
        if topics_list:
            filter_conditions.append(Filter.by_property("topics").contains_any(topics_list))
        
        # Star filters
        if min_stars is not None:
            filter_conditions.append(Filter.by_property("stars").greater_or_equal(min_stars))
        if max_stars is not None:
            filter_conditions.append(Filter.by_property("stars").less_or_equal(max_stars))
        
        # Fork filters
        if min_forks is not None:
            filter_conditions.append(Filter.by_property("forks").greater_or_equal(min_forks))
        if max_forks is not None:
            filter_conditions.append(Filter.by_property("forks").less_or_equal(max_forks))
        
        # License filter
        if license:
            filter_conditions.append(Filter.by_property("license").equal(license))
        
        # Boolean filters
        if has_issues is not None:
            filter_conditions.append(Filter.by_property("has_issues").equal(has_issues))
        if has_wiki is not None:
            filter_conditions.append(Filter.by_property("has_wiki").equal(has_wiki))
        if is_underrated is not None:
            filter_conditions.append(Filter.by_property("is_underrated").equal(is_underrated))
        if is_gsoc is not None:
            filter_conditions.append(Filter.by_property("is_gsoc").equal(is_gsoc))
        if is_hacktoberfest is not None:
            filter_conditions.append(Filter.by_property("is_hacktoberfest").equal(is_hacktoberfest))
        if has_good_first_issues is not None:
            filter_conditions.append(Filter.by_property("has_good_first_issues").equal(has_good_first_issues))
        
        # Text search filters
        if name_contains:
            filter_conditions.append(Filter.by_property("name").like(f"*{name_contains.lower()}*"))
        if description_contains:
            filter_conditions.append(Filter.by_property("description").like(f"*{description_contains.lower()}*"))
        
        # Combine all filter conditions with AND
        combined_filter = None
        if filter_conditions:
            combined_filter = filter_conditions[0]
            for condition in filter_conditions[1:]:
                combined_filter = combined_filter & condition
        
        # Get total count (with filters if applied)
        if combined_filter:
            total_count_response = collection.aggregate.over_all(
                filters=combined_filter,
                total_count=True
            )
        else:
            total_count_response = collection.aggregate.over_all(total_count=True)
        
        total_count = total_count_response.total_count
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
        has_next = page < total_pages
        has_prev = page > 1
        
        # Build sort configuration
        sort_ascending = sort_order == "asc"
        sort_config = Sort.by_property(sort_by, ascending=sort_ascending)
        
        # Query repositories with filters, pagination and sorting
        query_params = {
            'limit': limit,
            'offset': offset,
            'sort': sort_config,
            'return_properties': [
                "name", "full_name", "description", "url", "homepage",
                "language", "languages", "topics", "stars", "forks",
                "open_issues", "license", "has_issues", "has_wiki",
                "created_at", "updated_at", "is_underrated", "is_gsoc",
                "is_hacktoberfest", "has_good_first_issues"
            ]
        }
        
        if combined_filter:
            query_params['filters'] = combined_filter
        
        response = collection.query.fetch_objects(**query_params)
        
        # Format results
        repositories = []
        for obj in response.objects:
            props = obj.properties
            
            # Format topics and languages as lists
            topics = []
            if props.get('topics'):
                topics = [topic.strip() for topic in props['topics'].split(',') if topic.strip()]
            
            languages = []
            if props.get('languages'):
                languages = [lang.strip() for lang in props['languages'].split(',') if lang.strip()]
            
            repo = Repository(
                name=props.get('name') or '',
                full_name=props.get('full_name') or '',
                description=props.get('description') or '',
                url=props.get('url') or '',
                homepage=props.get('homepage') or '',
                language=props.get('language') or '',
                languages=languages,
                topics=topics,
                stars=props.get('stars') or 0,
                forks=props.get('forks') or 0,
                open_issues=props.get('open_issues') or 0,
                license=props.get('license') or '',
                has_issues=props.get('has_issues') or False,
                has_wiki=props.get('has_wiki') or False,
                created_at=props.get('created_at') or '',
                updated_at=props.get('updated_at') or ''
            )
            repositories.append(repo)
        
        # Build pagination info
        pagination_info = {
            "current_page": page,
            "per_page": limit,
            "total_items": total_count,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_prev,
            "next_page": page + 1 if has_next else None,
            "previous_page": page - 1 if has_prev else None,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        logger.info(f"Successfully retrieved {len(repositories)} repositories (page {page} of {total_pages}, {total_count} total with filters)")
        
        return PaginatedResponse(
            success=True,
            data=repositories,
            pagination=pagination_info,
            filters_applied=filters_applied if filters_applied else None
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in /allrepos endpoint: {str(e)}")
        return PaginatedResponse(
            success=False,
            data=[],
            pagination={},
            filters_applied=None,
            error=f"Failed to fetch repositories: {str(e)}"
        )

@app.get("/hiddengem", response_model=PaginatedResponse)
async def get_hidden_gems(
    page: int = 1,
    limit: int = 20,
    sort_by: str = "stars",
    sort_order: str = "desc"
):
    """
    Get hidden gem repositories - underrated repositories that deserve more attention.
    
    Parameters:
    - page: Page number (starts from 1)
    - limit: Number of items per page (max 100)
    - sort_by: Sort by field (stars, forks, updated_at, created_at, name)
    - sort_order: Sort order (asc or desc)
    
    Returns paginated list of underrated repositories from Weaviate.
    """
    try:
        # Validate parameters
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        if sort_by not in ["stars", "forks", "updated_at", "created_at", "name"]:
            raise HTTPException(status_code=400, detail="Invalid sort_by field")
        if sort_order not in ["asc", "desc"]:
            raise HTTPException(status_code=400, detail="Sort order must be 'asc' or 'desc'")
        
        logger.info(f"Fetching hidden gems: page={page}, limit={limit}, sort_by={sort_by}, sort_order={sort_order}")
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get collection and import Filter
        collection = weaviate_service.client.collections.get("Repos")
        from weaviate.classes.query import Filter, Sort
        
        # Create filter for underrated repositories
        underrated_filter = Filter.by_property("is_underrated").equal(True)
        
        # First, get total count of underrated repos
        total_count_response = collection.aggregate.over_all(
            filters=underrated_filter,
            total_count=True
        )
        total_count = total_count_response.total_count
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
        has_next = page < total_pages
        has_prev = page > 1
        
        # Build sort configuration
        sort_ascending = sort_order == "asc"
        sort_config = Sort.by_property(sort_by, ascending=sort_ascending)
        
        # Query underrated repositories with pagination and sorting
        response = collection.query.fetch_objects(
            filters=underrated_filter,
            limit=limit,
            offset=offset,
            sort=sort_config,
            return_properties=[
                "name", "full_name", "description", "url", "homepage",
                "language", "languages", "topics", "stars", "forks",
                "open_issues", "license", "has_issues", "has_wiki",
                "created_at", "updated_at", "is_underrated"
            ]
        )
        
        # Format results
        repositories = []
        for obj in response.objects:
            props = obj.properties
            
            # Format topics and languages as lists
            topics = []
            if props.get('topics'):
                topics = [topic.strip() for topic in props['topics'].split(',') if topic.strip()]
            
            languages = []
            if props.get('languages'):
                languages = [lang.strip() for lang in props['languages'].split(',') if lang.strip()]
            
            repo = Repository(
                name=props.get('name') or '',
                full_name=props.get('full_name') or '',
                description=props.get('description') or '',
                url=props.get('url') or '',
                homepage=props.get('homepage') or '',
                language=props.get('language') or '',
                languages=languages,
                topics=topics,
                stars=props.get('stars') or 0,
                forks=props.get('forks') or 0,
                open_issues=props.get('open_issues') or 0,
                license=props.get('license') or '',
                has_issues=props.get('has_issues') or False,
                has_wiki=props.get('has_wiki') or False,
                created_at=props.get('created_at') or '',
                updated_at=props.get('updated_at') or ''
            )
            repositories.append(repo)
        
        # Build pagination info
        pagination_info = {
            "current_page": page,
            "per_page": limit,
            "total_items": total_count,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_prev,
            "next_page": page + 1 if has_next else None,
            "previous_page": page - 1 if has_prev else None,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        logger.info(f"Successfully retrieved {len(repositories)} hidden gems (page {page} of {total_pages})")
        
        return PaginatedResponse(
            success=True,
            data=repositories,
            pagination=pagination_info
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in /hiddengem endpoint: {str(e)}")
        return PaginatedResponse(
            success=False,
            data=[],
            pagination={},
            error=f"Failed to fetch hidden gems: {str(e)}"
        )

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    try:
        weaviate_service.close()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Additional utility endpoints
@app.get("/example-queries")
async def get_example_queries():
    """Get example queries that work well with the system"""
    return {
        "examples": [
            {
                "query": "Find popular Python machine learning libraries",
                "description": "Searches for ML libraries in Python with good popularity"
            },
            {
                "query": "JavaScript frameworks with more than 1000 stars",
                "description": "Filters JavaScript frameworks by star count"
            },
            {
                "query": "I'm a frontend developer, show me open source tools",
                "description": "Semantic search for frontend development tools"
            },
            {
                "query": "Docker and Kubernetes repositories with good documentation",
                "description": "Finds containerization tools with documentation"
            },
            {
                "query": "CI/CD pipelines and automation tools",
                "description": "Searches for DevOps and automation repositories"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)