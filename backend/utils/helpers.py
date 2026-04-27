from typing import Dict, Any, List
from models import RepositoryResponse

def transform_repo_to_response(repo: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a MongoDB repository document to the API response format.
    
    Args:
        repo: Repository document from MongoDB
        
    Returns:
        Dictionary matching RepositoryResponse schema
    """
    owner = repo.get("owner", "")
    name = repo.get("name", "")
    
    # Construct full_name and URL
    full_name = f"{owner}/{name}" if owner and name else name
    url = f"https://github.com/{full_name}" if full_name else ""
    
    # Get primary language (first in languages list or None)
    languages = repo.get("languages", [])
    primary_language = languages[0] if languages else None
    
    return {
        "name": name,
        "full_name": full_name,
        "description": repo.get("description", ""),
        "url": url,
        "language": primary_language,
        "languages": languages,
        "topics": repo.get("topics", []),
        "stars": repo.get("stars", 0),
        "forks": repo.get("forks", 0),
        "open_issues": repo.get("issues", 0),
        "updated_at": repo.get("pushed_at", "")
    }

def transform_repos_list(repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform a list of repository documents to API response format.
    
    Args:
        repos: List of repository documents
        
    Returns:
        List of transformed repository dictionaries
    """
    return [transform_repo_to_response(repo) for repo in repos]

def calculate_pagination_metadata(
    current_page: int,
    per_page: int,
    total_items: int,
    sort_by: str,
    sort_order: str
) -> Dict[str, Any]:
    """
    Calculate pagination metadata.
    
    Args:
        current_page: Current page number (1-indexed)
        per_page: Items per page
        total_items: Total number of items
        sort_by: Sort field
        sort_order: Sort direction
        
    Returns:
        Pagination metadata dictionary
    """
    total_pages = (total_items + per_page - 1) // per_page  # Ceiling division
    has_next = current_page < total_pages
    has_previous = current_page > 1
    
    return {
        "current_page": current_page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_previous": has_previous,
        "next_page": current_page + 1 if has_next else None,
        "previous_page": current_page - 1 if has_previous else None,
        "sort_by": sort_by,
        "sort_order": sort_order
    }