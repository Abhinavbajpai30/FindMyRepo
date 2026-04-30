import logging
from typing import List, Dict, Any
from pymongo.collection import Collection
from utils.embeddings import embedding_generator

logger = logging.getLogger(__name__)

VECTOR_INDEX_NAME = "embedding_vector_index"


class SearchService:
    """Semantic search via MongoDB Atlas Vector Search ($vectorSearch aggregation)."""

    def __init__(self, collection: Collection):
        self.collection = collection

    def search(self, query: str, limit: int = 60) -> List[Dict[str, Any]]:
        """
        Embed the query with all-MiniLM-L6-v2 and run $vectorSearch across
        all documents in the collection. Returns up to `limit` results ordered
        by cosine similarity, each annotated with a `similarity_score`.
        """
        try:
            logger.info(f"Generating embedding for query: {query!r}")
            query_embedding = embedding_generator.generate(query)

            pipeline = [
                {
                    "$vectorSearch": {
                        "index": VECTOR_INDEX_NAME,
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": limit * 10,
                        "limit": limit,
                    }
                },
                {
                    "$addFields": {
                        "similarity_score": {"$meta": "vectorSearchScore"}
                    }
                },
                {
                    "$project": {
                        "name": 1, "owner": 1, "description": 1, "stars": 1,
                        "languages": 1, "topics": 1, "issues": 1, "pushed_at": 1,
                        "_id": 0, "similarity_score": 1,
                    }
                },
            ]

            results = list(self.collection.aggregate(pipeline))
            logger.info(f"$vectorSearch returned {len(results)} results")
            if results:
                logger.info(
                    f"Top result: {results[0].get('name')} "
                    f"(score: {results[0].get('similarity_score', 0):.4f})"
                )
            return results

        except Exception as e:
            logger.error(f"Error in search service: {e}")
            raise


# Service will be initialized in main.py with collection
