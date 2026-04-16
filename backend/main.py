import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from models import (
    SearchRequest, SearchResponse,
    UserPreferencesRequest, UserPreferencesResponse,
    AllReposResponse, HiddenGemsResponse,
    ErrorResponse
)
from database import db_instance
from services.search import SearchService
from services.recommendations import RecommendationService
from services.repository import RepositoryService
from utils.helpers import transform_repos_list, calculate_pagination_metadata

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FindMyRepo API",
    description="Backend API for GitHub repository discovery and recommendations",
    version="1.0.0"
)

# CORS Configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances (initialized on startup)
search_service: Optional[SearchService] = None
recommendation_service: Optional[RecommendationService] = None
repository_service: Optional[RepositoryService] = None

@app.on_event("startup")
async def startup_event():
    """Initialize database connection and services on startup"""
    global search_service, recommendation_service, repository_service
    
    try:
        logger.info("Starting up application...")
        
        # Connect to database
        db_instance.connect()
        collection = db_instance.get_collection()
        
        # Initialize services
        search_service = SearchService(collection)
        recommendation_service = RecommendationService(collection)
        repository_service = RepositoryService(collection)
        
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logger.info("Shutting down application...")
    db_instance.disconnect()
    logger.info("Application shutdown complete")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "FindMyRepo API is running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check database connection
        collection = db_instance.get_collection()
        count = collection.count_documents({})
        
        return {
            "status": "healthy",
            "database": "connected",
            "repositories_count": count
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.post("/search", response_model=SearchResponse)
async def search_repositories(request: SearchRequest):
    """
    Search for repositories using natural language query.
    
    This endpoint:
    1. Generates query embedding for vector similarity
    2. Uses Gemini AI to create a MongoDB filter query
    3. Combines both approaches to return relevant repositories
    """
    try:
        logger.info(f"Search request received: {request.query}")
        
        if not search_service:
            raise HTTPException(status_code=503, detail="Search service not initialized")
        
        # Perform search
        results = search_service.search(request.query, limit=20)
        
        # Transform to response format
        transformed_results = transform_repos_list(results)
        
        return SearchResponse(success=True, results=transformed_results)
        
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/userpreferences", response_model=UserPreferencesResponse)
async def get_personalized_recommendations(request: UserPreferencesRequest):
    """
    Get personalized repository recommendations based on user preferences.
    
    This endpoint:
    1. Uses Gemini AI to generate a MongoDB query based on user preferences
    2. Matches repositories by languages, domains, and expertise level
    3. Returns repositories ranked by relevance to user preferences
    """
    try:
        logger.info(f"User preferences request received")
        logger.info(f"Domains: {request.primaryDomains}")
        logger.info(f"Role: {request.role}")
        logger.info(f"Expertise: {request.expertise}")
        logger.info(f"Languages: {request.preferredLanguages}")
        
        if not recommendation_service:
            raise HTTPException(status_code=503, detail="Recommendation service not initialized")
        
        # Convert request to dict
        preferences = request.model_dump()
        
        # Get personalized recommendations
        results = recommendation_service.get_personalized_repos(preferences, limit=20)
        
        # Transform to response format
        transformed_results = transform_repos_list(results)
        
        return UserPreferencesResponse(success=True, results=transformed_results)
        
    except Exception as e:
        logger.error(f"Error in user preferences endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@app.get("/allrepos", response_model=AllReposResponse)
async def get_all_repositories(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("stars", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    languages: Optional[str] = Query(None, description="Comma-separated language names"),
    topics: Optional[str] = Query(None, description="Comma-separated topic names"),
    min_stars: Optional[int] = Query(None, ge=0, description="Minimum stars"),
    max_stars: Optional[int] = Query(None, ge=0, description="Maximum stars"),
    name_contains: Optional[str] = Query(None, description="Repository name contains"),
    description_contains: Optional[str] = Query(None, description="Description contains"),
    is_hacktoberfest: Optional[bool] = Query(None, description="Hacktoberfest repos"),
    is_gsoc: Optional[bool] = Query(None, description="Google Summer of Code repos"),
    is_underrated: Optional[bool] = Query(None, description="Underrated repos")
):
    """
    Get all repositories with pagination, sorting, and filtering.
    
    Supports filtering by:
    - Programming languages
    - Topics/tags
    - Star range
    - Name/description search
    - Special categories (Hacktoberfest, GSOC, underrated)
    """
    try:
        logger.info(f"All repos request: page={page}, limit={limit}, sort_by={sort_by}")
        
        if not repository_service:
            raise HTTPException(status_code=503, detail="Repository service not initialized")
        
        # Build filters dictionary
        filters = {
            "languages": languages,
            "topics": topics,
            "min_stars": min_stars,
            "max_stars": max_stars,
            "name_contains": name_contains,
            "description_contains": description_contains,
            "is_hacktoberfest": is_hacktoberfest,
            "is_gsoc": is_gsoc,
            "is_underrated": is_underrated
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Get repositories
        results, total_count = repository_service.get_all_repos(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters
        )
        
        # Transform results
        transformed_results = transform_repos_list(results)
        
        # Calculate pagination metadata
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
        
    except Exception as e:
        logger.error(f"Error in all repos endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch repositories: {str(e)}")

@app.get("/hiddengem", response_model=HiddenGemsResponse)
async def get_hidden_gems(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("stars", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """
    Get "hidden gem" repositories - high quality projects with < 1000 stars.
    
    Hidden gems are defined as repositories that:
    - Have between 100-1000 stars
    - Are recently updated (within last 18 months)
    - Have good documentation (non-empty README)
    - Show active engagement (has issues)
    """
    try:
        logger.info(f"Hidden gems request: page={page}, limit={limit}, sort_by={sort_by}")
        
        if not repository_service:
            raise HTTPException(status_code=503, detail="Repository service not initialized")
        
        # Get hidden gems
        results, total_count = repository_service.get_hidden_gems(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Transform results
        transformed_results = transform_repos_list(results)
        
        # Calculate pagination metadata
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
        
    except Exception as e:
        logger.error(f"Error in hidden gems endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch hidden gems: {str(e)}")

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)