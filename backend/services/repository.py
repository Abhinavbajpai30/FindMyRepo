import logging
from typing import List, Dict, Any, Optional
from pymongo.collection import Collection

logger = logging.getLogger(__name__)

class RepositoryService:
    """Handles repository listing, filtering, and pagination"""
    
    def __init__(self, collection: Collection):
        self.collection = collection
    
    def get_all_repos(
        self,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "stars",
        sort_order: str = "desc",
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get all repositories with pagination, sorting, and filtering.
        
        Args:
            page: Page number (1-indexed)
            limit: Items per page
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'
            filters: Optional filter dictionary
            
        Returns:
            Tuple of (results list, total count)
        """
        try:
            # Build MongoDB filter
            mongo_filter = self._build_filter(filters or {})
            
            # Calculate skip
            skip = (page - 1) * limit
            
            # Sort direction
            sort_direction = -1 if sort_order == "desc" else 1
            
            # Get total count
            total_count = self.collection.count_documents(mongo_filter)
            
            logger.info(f"Querying all repos: page={page}, limit={limit}, sort_by={sort_by}, "
                       f"filter_count={len(mongo_filter)}, total={total_count}")
            
            # Query with pagination
            cursor = self.collection.find(
                mongo_filter,
                {
                    "name": 1,
                    "owner": 1,
                    "description": 1,
                    "stars": 1,
                    "languages": 1,
                    "topics": 1,
                    "issues": 1,
                    "pushed_at": 1,
                    "_id": 0
                }
            ).sort(sort_by, sort_direction).skip(skip).limit(limit)
            
            results = list(cursor)
            
            logger.info(f"Returning {len(results)} repositories from page {page}")
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Error in get_all_repos: {e}")
            raise
    
    def get_hidden_gems(
        self,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "stars",
        sort_order: str = "desc"
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get "hidden gem" repositories (< 1000 stars but high quality).
        
        Criteria for hidden gems:
        - Stars between 100 and 1000
        - Recently updated (within last 18 months)
        - Has good documentation (non-empty readme)
        - Active issues (shows engagement)
        - At least 2 languages (shows complexity)
        
        Args:
            page: Page number (1-indexed)
            limit: Items per page
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'
            
        Returns:
            Tuple of (results list, total count)
        """
        try:
            # Build filter for hidden gems
            mongo_filter = {
                "stars": {"$gte": 100, "$lt": 1000},
                "pushed_at": {"$gte": "2023-06-01"},  # Updated in last ~18 months
                "readme": {"$exists": True, "$ne": None, "$ne": ""},
                "issues": {"$gte": 1}  # Has at least some issues (engagement)
            }
            
            # Calculate skip
            skip = (page - 1) * limit
            
            # Sort direction
            sort_direction = -1 if sort_order == "desc" else 1
            
            # Get total count
            total_count = self.collection.count_documents(mongo_filter)
            
            logger.info(f"Querying hidden gems: page={page}, limit={limit}, sort_by={sort_by}, total={total_count}")
            
            # Query with pagination
            cursor = self.collection.find(
                mongo_filter,
                {
                    "name": 1,
                    "owner": 1,
                    "description": 1,
                    "stars": 1,
                    "languages": 1,
                    "topics": 1,
                    "issues": 1,
                    "pushed_at": 1,
                    "_id": 0
                }
            ).sort(sort_by, sort_direction).skip(skip).limit(limit)
            
            results = list(cursor)
            
            logger.info(f"Returning {len(results)} hidden gems from page {page}")
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Error in get_hidden_gems: {e}")
            raise
    
    def _build_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build MongoDB filter from query parameters.
        
        Args:
            filters: Dictionary of filter parameters
            
        Returns:
            MongoDB filter object
        """
        mongo_filter = {}
        
        # Languages filter
        if "languages" in filters and filters["languages"]:
            languages_list = [lang.strip() for lang in filters["languages"].split(",") if lang.strip()]
            if languages_list:
                mongo_filter["languages"] = {"$in": languages_list}
        
        # Topics filter
        if "topics" in filters and filters["topics"]:
            topics_list = [topic.strip() for topic in filters["topics"].split(",") if topic.strip()]
            if topics_list:
                mongo_filter["topics"] = {"$in": topics_list}
        
        # Star range
        star_conditions = {}
        if "min_stars" in filters and filters["min_stars"] is not None:
            star_conditions["$gte"] = int(filters["min_stars"])
        if "max_stars" in filters and filters["max_stars"] is not None:
            star_conditions["$lte"] = int(filters["max_stars"])
        if star_conditions:
            mongo_filter["stars"] = star_conditions
        
        # Fork range (note: forks field might not exist in current schema)
        # We'll skip this for now as it's not in the ingestion script
        
        # Name contains
        if "name_contains" in filters and filters["name_contains"]:
            mongo_filter["name"] = {"$regex": filters["name_contains"], "$options": "i"}
        
        # Description contains
        if "description_contains" in filters and filters["description_contains"]:
            mongo_filter["description"] = {"$regex": filters["description_contains"], "$options": "i"}
        
        # Boolean flags
        if "is_hacktoberfest" in filters and filters["is_hacktoberfest"]:
            mongo_filter["topics"] = {"$in": ["hacktoberfest"]}
        
        if "is_gsoc" in filters and filters["is_gsoc"]:
            mongo_filter["topics"] = {"$in": ["gsoc", "google-summer-of-code"]}
        
        # Underrated repos (high quality but low stars)
        if "is_underrated" in filters and filters["is_underrated"]:
            mongo_filter["stars"] = {"$gte": 50, "$lt": 500}
            mongo_filter["pushed_at"] = {"$gte": "2023-01-01"}
        
        return mongo_filter

# Service will be initialized in main.py