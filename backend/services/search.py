import logging
from typing import List, Dict, Any
from pymongo.collection import Collection
from utils.gemini_service import gemini_generator
from utils.embeddings import embedding_generator

logger = logging.getLogger(__name__)

class SearchService:
    """Handles search operations combining MongoDB filtering with vector similarity"""
    
    def __init__(self, collection: Collection):
        self.collection = collection
    
    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Perform hybrid search: Gemini-generated MongoDB query + vector similarity ranking.
        
        Args:
            query: User's search query
            limit: Maximum number of results to return
            
        Returns:
            List of repository documents sorted by relevance
        """
        try:
            # Step 1: Generate query embedding for vector similarity
            logger.info(f"Generating embedding for query: {query}")
            query_embedding = embedding_generator.generate(query)
            
            # Step 2: Use Gemini to generate MongoDB filter query
            logger.info(f"Generating MongoDB query using Gemini for: {query}")
            gemini_query = gemini_generator.generate_search_query(query)
            
            mongo_filter = gemini_query.get("filter", {})
            mongo_sort = gemini_query.get("sort", {"stars": -1})
            
            logger.info(f"MongoDB Filter: {mongo_filter}")
            logger.info(f"MongoDB Sort: {mongo_sort}")
            
            # Step 3: Query MongoDB with the generated filter
            # First, get a larger pool of candidates (3x the limit)
            candidate_limit = limit * 3
            
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
                    "embedding": 1,
                    "_id": 0
                }
            ).sort(list(mongo_sort.items())).limit(candidate_limit)
            
            candidates = list(cursor)
            logger.info(f"Found {len(candidates)} candidate repositories")
            
            if not candidates:
                logger.warning("No repositories found matching the filter")
                return []
            
            # Step 4: Calculate vector similarity for each candidate
            for repo in candidates:
                if "embedding" in repo and repo["embedding"]:
                    similarity = embedding_generator.calculate_similarity(
                        query_embedding, 
                        repo["embedding"]
                    )
                    repo["similarity_score"] = similarity
                else:
                    repo["similarity_score"] = 0.0
                
                # Remove embedding from response (too large)
                repo.pop("embedding", None)
            
            # Step 5: Re-rank by similarity score
            candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Step 6: Return top results
            results = candidates[:limit]
            
            logger.info(f"Returning top {len(results)} results")
            if results:
                logger.info(f"Top result: {results[0].get('name')} (similarity: {results[0].get('similarity_score', 0):.4f})")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in search service: {e}")
            raise
    
    def search_with_filters(
        self, 
        base_filter: Dict[str, Any],
        sort_by: str = "stars",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Search with explicit filters (used by /allrepos endpoint).
        
        Args:
            base_filter: MongoDB filter object
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'
            page: Page number (1-indexed)
            limit: Results per page
            
        Returns:
            Tuple of (results list, total count)
        """
        try:
            # Calculate skip value
            skip = (page - 1) * limit
            
            # Sort direction
            sort_direction = -1 if sort_order == "desc" else 1
            
            # Get total count
            total_count = self.collection.count_documents(base_filter)
            
            # Query with pagination
            cursor = self.collection.find(
                base_filter,
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
            
            logger.info(f"Found {total_count} total results, returning page {page} ({len(results)} items)")
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Error in search_with_filters: {e}")
            raise

# Service will be initialized in main.py with collection