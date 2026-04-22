import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pymongo.collection import Collection

logger = logging.getLogger(__name__)


def _recent_cutoff(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")


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
        try:
            mongo_filter = self._build_filter(filters or {})
            skip = (page - 1) * limit
            sort_direction = -1 if sort_order == "desc" else 1

            total_count = self.collection.count_documents(mongo_filter)

            logger.info(f"Querying all repos: page={page}, limit={limit}, sort_by={sort_by}, "
                        f"filter_count={len(mongo_filter)}, total={total_count}")

            cursor = self.collection.find(
                mongo_filter,
                {
                    "name": 1, "owner": 1, "description": 1, "stars": 1,
                    "languages": 1, "topics": 1, "issues": 1, "pushed_at": 1, "_id": 0
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
        try:
            mongo_filter = {
                "stars": {"$gte": 100, "$lt": 1000},
                "pushed_at": {"$gte": _recent_cutoff(548)},  # ~18 months
                "readme": {"$exists": True, "$nin": [None, ""]},
                "issues": {"$gte": 1}
            }

            skip = (page - 1) * limit
            sort_direction = -1 if sort_order == "desc" else 1
            total_count = self.collection.count_documents(mongo_filter)

            logger.info(f"Querying hidden gems: page={page}, limit={limit}, sort_by={sort_by}, total={total_count}")

            cursor = self.collection.find(
                mongo_filter,
                {
                    "name": 1, "owner": 1, "description": 1, "stars": 1,
                    "languages": 1, "topics": 1, "issues": 1, "pushed_at": 1, "_id": 0
                }
            ).sort(sort_by, sort_direction).skip(skip).limit(limit)

            results = list(cursor)
            logger.info(f"Returning {len(results)} hidden gems from page {page}")
            return results, total_count

        except Exception as e:
            logger.error(f"Error in get_hidden_gems: {e}")
            raise

    def _build_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        mongo_filter = {}
        topic_conditions = []

        # Languages filter
        if filters.get("languages"):
            languages_list = [lang.strip() for lang in filters["languages"].split(",") if lang.strip()]
            if languages_list:
                mongo_filter["languages"] = {"$in": languages_list}

        # Explicit topics filter
        if filters.get("topics"):
            topics_list = [topic.strip() for topic in filters["topics"].split(",") if topic.strip()]
            if topics_list:
                topic_conditions.append({"topics": {"$in": topics_list}})

        # Star range
        star_conditions = {}
        if filters.get("min_stars") is not None:
            star_conditions["$gte"] = int(filters["min_stars"])
        if filters.get("max_stars") is not None:
            star_conditions["$lte"] = int(filters["max_stars"])
        if star_conditions:
            mongo_filter["stars"] = star_conditions

        # Name / description text search
        if filters.get("name_contains"):
            mongo_filter["name"] = {"$regex": filters["name_contains"], "$options": "i"}
        if filters.get("description_contains"):
            mongo_filter["description"] = {"$regex": filters["description_contains"], "$options": "i"}

        # Boolean category flags — collect topic conditions to merge with $and
        if filters.get("is_hacktoberfest"):
            topic_conditions.append({"topics": {"$in": ["hacktoberfest"]}})

        if filters.get("is_gsoc"):
            topic_conditions.append({"topics": {"$in": ["gsoc", "google-summer-of-code"]}})

        # Merge all topic conditions
        if len(topic_conditions) == 1:
            mongo_filter.update(topic_conditions[0])
        elif len(topic_conditions) > 1:
            mongo_filter["$and"] = topic_conditions

        # Underrated: override stars only if not already set
        if filters.get("is_underrated"):
            mongo_filter["stars"] = {"$gte": 50, "$lt": 500}
            mongo_filter["pushed_at"] = {"$gte": _recent_cutoff(730)}  # ~2 years

        return mongo_filter


# Service will be initialized in main.py
