import os
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables before importing services that require them at import time.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from models import (
    SearchRequest, SearchResponse,
    UserPreferencesRequest, UserPreferencesResponse,
    AllReposResponse, HiddenGemsResponse,
    RepoDetailResponse,
)
from database import db_instance
from services.search import SearchService
from services.recommendations import RecommendationService
from services.repository import RepositoryService
from utils.helpers import transform_repo_to_response, transform_repos_list, calculate_pagination_metadata

# Frontend sort values use response field names (updated_at, open_issues).
# The service maps these internally to MongoDB field names.
ALLOWED_SORT_FIELDS = {
    "stars", "forks", "name", "issues",
    "updated_at",    # mapped → pushed_at in MongoDB
    "open_issues",   # mapped → issues in MongoDB
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances (initialized on startup)
search_service: Optional[SearchService] = None
recommendation_service: Optional[RecommendationService] = None
repository_service: Optional[RepositoryService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global search_service, recommendation_service, repository_service
    try:
        logger.info("Starting up application...")
        db_instance.connect()
        collection = db_instance.get_collection()
        search_service = SearchService(collection)
        recommendation_service = RecommendationService(collection)
        repository_service = RepositoryService(collection)
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    yield
    logger.info("Shutting down application...")
    db_instance.disconnect()
    logger.info("Application shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="FindMyRepo API",
    description="Backend API for GitHub repository discovery and recommendations",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "FindMyRepo API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    try:
        collection = db_instance.get_collection()
        count = collection.estimated_document_count()
        return {
            "status": "healthy",
            "database": "connected",
            "repositories_count": count
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": "Database connection failed"}
        )


@app.post("/search", response_model=SearchResponse)
async def search_repositories(request: SearchRequest):
    try:
        logger.info(f"Search request received: {request.query}")

        if not search_service:
            raise HTTPException(status_code=503, detail="Search service not initialized")

        results = await asyncio.to_thread(search_service.search, request.query, 20)
        transformed_results = transform_repos_list(results)
        return SearchResponse(success=True, results=transformed_results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@app.post("/userpreferences", response_model=UserPreferencesResponse)
async def get_personalized_recommendations(request: UserPreferencesRequest):
    try:
        logger.info(f"User preferences request received")
        logger.info(f"Domains: {request.primaryDomains}")
        logger.info(f"Role: {request.role}")
        logger.info(f"Expertise: {request.expertise}")
        logger.info(f"Languages: {request.preferredLanguages}")

        if not recommendation_service:
            raise HTTPException(status_code=503, detail="Recommendation service not initialized")

        preferences = request.model_dump()
        results = await asyncio.to_thread(
            recommendation_service.get_personalized_repos, preferences, 20
        )
        transformed_results = transform_repos_list(results)
        return UserPreferencesResponse(success=True, results=transformed_results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in user preferences endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


@app.get("/allrepos", response_model=AllReposResponse)
async def get_all_repositories(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("stars", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    languages: Optional[str] = Query(None, description="Comma-separated language names"),
    topics: Optional[str] = Query(None, description="Comma-separated topic names"),
    min_stars: Optional[int] = Query(None, ge=0, description="Minimum stars"),
    max_stars: Optional[int] = Query(None, ge=0, description="Maximum stars"),
    min_forks: Optional[int] = Query(None, ge=0, description="Minimum forks"),
    max_forks: Optional[int] = Query(None, ge=0, description="Maximum forks"),
    has_issues: Optional[bool] = Query(None, description="Only repos with open issues"),
    has_wiki: Optional[bool] = Query(None, description="Only repos with a wiki"),
    name_contains: Optional[str] = Query(None, description="Repository name contains"),
    description_contains: Optional[str] = Query(None, description="Description contains"),
    is_hacktoberfest: Optional[bool] = Query(None, description="Hacktoberfest repos"),
    is_gsoc: Optional[bool] = Query(None, description="Google Summer of Code repos"),
    is_underrated: Optional[bool] = Query(None, description="Underrated repos")
):
    if sort_by not in ALLOWED_SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by field. Allowed: {sorted(ALLOWED_SORT_FIELDS)}"
        )

    try:
        logger.info(f"All repos request: page={page}, limit={limit}, sort_by={sort_by}")

        if not repository_service:
            raise HTTPException(status_code=503, detail="Repository service not initialized")

        filters = {
            "languages": languages,
            "topics": topics,
            "min_stars": min_stars,
            "max_stars": max_stars,
            "min_forks": min_forks,
            "max_forks": max_forks,
            "has_issues": has_issues,
            "has_wiki": has_wiki,
            "name_contains": name_contains,
            "description_contains": description_contains,
            "is_hacktoberfest": is_hacktoberfest,
            "is_gsoc": is_gsoc,
            "is_underrated": is_underrated
        }
        filters = {k: v for k, v in filters.items() if v is not None}

        results, total_count = repository_service.get_all_repos(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters
        )

        transformed_results = transform_repos_list(results)
        pagination = calculate_pagination_metadata(
            current_page=page,
            per_page=limit,
            total_items=total_count,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return AllReposResponse(
            success=True,
            data=transformed_results,
            pagination=pagination,
            filters_applied=filters
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in all repos endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch repositories")


@app.get("/hiddengem", response_model=HiddenGemsResponse)
async def get_hidden_gems(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("stars", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order")
):
    if sort_by not in ALLOWED_SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by field. Allowed: {sorted(ALLOWED_SORT_FIELDS)}"
        )

    try:
        logger.info(f"Hidden gems request: page={page}, limit={limit}, sort_by={sort_by}")

        if not repository_service:
            raise HTTPException(status_code=503, detail="Repository service not initialized")

        results, total_count = repository_service.get_hidden_gems(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )

        transformed_results = transform_repos_list(results)
        pagination = calculate_pagination_metadata(
            current_page=page,
            per_page=limit,
            total_items=total_count,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return HiddenGemsResponse(
            success=True,
            data=transformed_results,
            pagination=pagination
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in hidden gems endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch hidden gems")


@app.get("/repo/{owner}/{name}", response_model=RepoDetailResponse)
async def get_repo_detail(owner: str, name: str):
    try:
        logger.info(f"Repo detail request: {owner}/{name}")

        if not repository_service:
            raise HTTPException(status_code=503, detail="Repository service not initialized")

        doc = repository_service.get_repo(owner, name)
        if doc is None:
            raise HTTPException(status_code=404, detail=f"Repository {owner}/{name} not found")

        transformed = transform_repo_to_response(doc)
        transformed["readme"] = doc.get("readme")
        return RepoDetailResponse(**transformed)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching repo detail {owner}/{name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch repository")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
