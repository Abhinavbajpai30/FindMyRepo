from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Request Models

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    limit: int = Field(default=60, ge=10, le=150, description="Maximum results to return")

class UserPreferencesRequest(BaseModel):
    primaryDomains: List[str] = Field(default_factory=list, description="User's primary domains of interest")
    role: str = Field(..., description="User's role")
    expertise: str = Field(..., description="User's expertise level")
    preferredLanguages: List[str] = Field(default_factory=list, description="User's preferred programming languages")

# Response Models

class RepositoryResponse(BaseModel):
    name: str
    full_name: str
    description: Optional[str] = None
    url: str
    language: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    updated_at: Optional[str] = None
    similarity_score: Optional[float] = None

class RepoDetailResponse(RepositoryResponse):
    readme: Optional[str] = None

class SearchResponse(BaseModel):
    success: bool = True
    results: List[RepositoryResponse]
    total_returned: int = 0

class UserPreferencesResponse(BaseModel):
    success: bool = True
    results: List[RepositoryResponse]

class PaginationMetadata(BaseModel):
    current_page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool
    next_page: Optional[int] = None
    previous_page: Optional[int] = None
    sort_by: str
    sort_order: str

class AllReposResponse(BaseModel):
    success: bool = True
    data: List[RepositoryResponse]
    pagination: PaginationMetadata
    filters_applied: Dict[str, Any] = Field(default_factory=dict)

class HiddenGemsResponse(BaseModel):
    success: bool = True
    data: List[RepositoryResponse]
    pagination: PaginationMetadata

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None