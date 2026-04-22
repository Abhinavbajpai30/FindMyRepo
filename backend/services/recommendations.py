import logging
from typing import List, Dict, Any
from pymongo.collection import Collection
from utils.gemini_service import gemini_generator

logger = logging.getLogger(__name__)

class RecommendationService:
    """Generates personalized repository recommendations based on user preferences"""
    
    def __init__(self, collection: Collection):
        self.collection = collection
    
    def get_personalized_repos(
        self, 
        preferences: Dict[str, Any],
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get personalized repository recommendations based on user preferences.
        
        Args:
            preferences: User preference data (domains, role, expertise, languages)
            limit: Maximum number of results
            
        Returns:
            List of recommended repositories
        """
        try:
            logger.info(f"Generating personalized recommendations for preferences: {preferences}")
            
            # Step 1: Use Gemini to generate MongoDB query based on preferences
            gemini_query = gemini_generator.generate_personalized_query(preferences)
            
            mongo_filter = gemini_query.get("filter", {})
            mongo_sort = gemini_query.get("sort", {"stars": -1})
            query_limit = gemini_query.get("limit", limit)
            
            logger.info(f"MongoDB Filter: {mongo_filter}")
            logger.info(f"MongoDB Sort: {mongo_sort}")
            logger.info(f"Explanation: {gemini_query.get('explanation', 'N/A')}")
            
            # Step 2: Query MongoDB
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
            ).sort(list(mongo_sort.items())).limit(query_limit)
            
            results = list(cursor)
            
            logger.info(f"Found {len(results)} personalized recommendations")
            
            # Step 3: Apply additional scoring based on preference matching
            for repo in results:
                score = self._calculate_preference_score(repo, preferences)
                repo["preference_score"] = score
            
            # Step 4: Re-rank by preference score
            results.sort(key=lambda x: x.get("preference_score", 0), reverse=True)
            
            # Step 5: Return top results
            final_results = results[:limit]
            
            # Remove internal scoring field
            for repo in final_results:
                repo.pop("preference_score", None)
            
            logger.info(f"Returning {len(final_results)} personalized recommendations")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error in recommendation service: {e}")
            raise
    
    def _calculate_preference_score(
        self, 
        repo: Dict[str, Any], 
        preferences: Dict[str, Any]
    ) -> float:
        """
        Calculate how well a repository matches user preferences.
        
        Args:
            repo: Repository document
            preferences: User preferences
            
        Returns:
            Score between 0 and 1
        """
        score = 0.0
        
        # Language match (weight: 0.4)
        preferred_languages = preferences.get("preferredLanguages", [])
        repo_languages = repo.get("languages", [])
        if preferred_languages and repo_languages:
            language_matches = len(set(preferred_languages) & set(repo_languages))
            language_score = language_matches / len(preferred_languages)
            score += language_score * 0.4
        
        # Domain/Topic match (weight: 0.3)
        primary_domains = preferences.get("primaryDomains", [])
        repo_topics = repo.get("topics", [])
        
        # Map domains to topic keywords
        domain_topic_map = {
            "Frontend / Web": ["frontend", "web", "react", "vue", "angular", "css", "html", "ui"],
            "Backend / APIs": ["backend", "api", "rest", "graphql", "server", "nodejs"],
            "Mobile (iOS/Android)": ["mobile", "ios", "android", "react-native", "flutter"],
            "ML / AI / Data Science": ["machine-learning", "deep-learning", "ai", "data-science"],
            "DevOps / Infrastructure": ["devops", "infrastructure", "kubernetes", "docker", "ci-cd"],
            "Game Development": ["game", "gamedev", "game-engine", "unity"],
            "Cybersecurity": ["security", "cybersecurity", "cryptography"]
        }
        
        if primary_domains and repo_topics:
            matching_topics = []
            for domain in primary_domains:
                domain_keywords = domain_topic_map.get(domain, [])
                matching_topics.extend([t for t in repo_topics if any(kw in t.lower() for kw in domain_keywords)])
            
            if matching_topics:
                topic_score = min(len(set(matching_topics)) / 3, 1.0)  # Cap at 1.0
                score += topic_score * 0.3
        
        # Popularity/Quality indicators (weight: 0.2)
        stars = repo.get("stars", 0)
        if stars >= 1000:
            popularity_score = min(stars / 10000, 1.0)  # Normalize
            score += popularity_score * 0.2
        
        # Recency (weight: 0.1)
        pushed_at = repo.get("pushed_at", "")
        if pushed_at and any(year in pushed_at for year in ["2024", "2025", "2026"]):
            score += 0.1
        
        return score

# Service will be initialized in main.py