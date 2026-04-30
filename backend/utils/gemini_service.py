import os
import json
import logging
from typing import Dict, Any, Optional
from google import genai

logger = logging.getLogger(__name__)

ALLOWED_FILTER_FIELDS = {
    "name", "owner", "description", "stars", "languages",
    "issues", "topics", "pushed_at", "forks",
}
ALLOWED_MONGO_LOGICAL_OPS = {"$and", "$or", "$nor"}
ALLOWED_SORT_FIELDS = {"stars", "forks", "pushed_at", "name", "issues", "watchers_count"}
MAX_QUERY_LENGTH = 500


def _sanitize_filter(filter_dict: Any) -> Dict[str, Any]:
    """Recursively strip any keys not in the field allowlist from a Gemini-generated filter."""
    if not isinstance(filter_dict, dict):
        return {}
    result = {}
    for key, value in filter_dict.items():
        if key in ALLOWED_MONGO_LOGICAL_OPS:
            if isinstance(value, list):
                result[key] = [_sanitize_filter(item) for item in value]
        elif key in ALLOWED_FILTER_FIELDS:
            result[key] = value
    return result


def _sanitize_sort(sort_dict: Any) -> Dict[str, int]:
    """Keep only allowed sort fields with valid directions."""
    if not isinstance(sort_dict, dict):
        return {"stars": -1}
    sanitized = {
        k: v for k, v in sort_dict.items()
        if k in ALLOWED_SORT_FIELDS and v in (1, -1)
    }
    return sanitized if sanitized else {"stars": -1}


class GeminiQueryGenerator:
    """Uses Google Gemini to generate MongoDB queries from natural language"""

    def __init__(self):
        self._api_key = os.getenv("GEMINI_API_KEY")
        self._client = None
        self.model = "gemini-flash-latest"
        if self._api_key:
            self._client = genai.Client(api_key=self._api_key)
            logger.info("Gemini AI initialized successfully")
        else:
            logger.warning("GEMINI_API_KEY not set — Gemini features unavailable")

    @property
    def client(self):
        if self._client is None:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        return self._client

    def generate_search_query(self, user_query: str) -> Dict[str, Any]:
        """
        Generate MongoDB query for semantic search based on user's natural language query.
        """
        safe_query = user_query[:MAX_QUERY_LENGTH].replace('"', '\\"')

        prompt = f"""You are a MongoDB query expert. Given a user's search query for finding GitHub repositories,
generate a MongoDB aggregation pipeline that will find the most relevant repositories.

The MongoDB collection schema is:
- name (string): Repository name
- owner (string): Repository owner
- description (string): Repository description
- stars (int): Number of stars
- languages (array of strings): Programming languages used
- issues (int): Number of open issues
- topics (array of strings): Repository topics/tags
- pushed_at (string): Last push date
- readme (string): README content (cleaned)

Your task:
1. Parse the user query to extract:
   - Programming languages mentioned (JavaScript, Python, Go, Rust, TypeScript, Java, C++, C#, Ruby, PHP, Swift, Kotlin, etc.)
   - Topics/domains (web-development, machine-learning, devops, api, cli, database, security, etc.)
   - Project type keywords (framework, library, tool, application, etc.)
   - Size preferences (popular, trending, stars count)

2. Generate a MongoDB filter query (NOT aggregation pipeline) that includes:
   - Language filters using $in operator on 'languages' array
   - Topic filters using $all or $in operator on 'topics' array
   - Star range using $gte and $lte on 'stars' field
   - Text search on 'name' and 'description' fields using $regex (case-insensitive)

3. Return ONLY a valid JSON object with these fields:
   - "filter": MongoDB filter query object
   - "sort": Sort criteria (e.g., {{"stars": -1}})
   - "explanation": Brief explanation of the query logic

Rules:
- Use case-insensitive regex for text matching: {{"$regex": "pattern", "$options": "i"}}
- For multiple conditions, use $and or $or appropriately
- Default sort by stars descending if not specified
- Keep the query simple and efficient
- DO NOT include vector search operations (those are handled separately)
- Return ONLY valid JSON, no markdown, no explanations outside the JSON

User Query: "{safe_query}"

Output JSON:"""

        try:
            response = self.client.models.generate_content(model=self.model, contents=prompt)
            response_text = response.text.strip()

            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            query_data = json.loads(response_text)

            query_data["filter"] = _sanitize_filter(query_data.get("filter", {}))
            query_data["sort"] = _sanitize_sort(query_data.get("sort", {"stars": -1}))

            logger.info(f"Generated query for '{user_query}': {json.dumps(query_data, indent=2)}")
            return query_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            return {
                "filter": {
                    "$or": [
                        {"name": {"$regex": safe_query, "$options": "i"}},
                        {"description": {"$regex": safe_query, "$options": "i"}}
                    ]
                },
                "sort": {"stars": -1},
                "explanation": "Fallback query due to parsing error"
            }
        except Exception as e:
            logger.error(f"Error generating query with Gemini: {e}")
            raise

    def generate_personalized_query(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate MongoDB query based on user preferences for personalized recommendations.
        """
        safe_preferences = {
            k: v for k, v in preferences.items()
            if isinstance(v, (str, int, float, bool, list))
        }

        prompt = f"""You are a MongoDB query expert specializing in personalized recommendations.
Given a user's preferences for finding GitHub repositories, generate a MongoDB query that matches their interests.

The MongoDB collection schema is:
- name (string): Repository name
- owner (string): Repository owner
- description (string): Repository description
- stars (int): Number of stars
- languages (array of strings): Programming languages used
- issues (int): Number of open issues
- topics (array of strings): Repository topics/tags
- pushed_at (string): Last push date (ISO format)
- readme (string): README content

User Preferences:
{json.dumps(safe_preferences, indent=2)}

Domain to Topic Mapping (use these to map user domains to repository topics):
- "Frontend / Web" → ["frontend", "web", "react", "vue", "angular", "css", "html", "ui", "ux"]
- "Backend / APIs" → ["backend", "api", "rest", "graphql", "server", "nodejs", "express", "fastapi", "django"]
- "Mobile (iOS/Android)" → ["mobile", "ios", "android", "react-native", "flutter", "swift", "kotlin"]
- "ML / AI / Data Science" → ["machine-learning", "deep-learning", "artificial-intelligence", "data-science", "pytorch", "tensorflow", "nlp"]
- "DevOps / Infrastructure" → ["devops", "infrastructure", "kubernetes", "docker", "ci-cd", "terraform", "monitoring"]
- "Game Development" → ["game", "gamedev", "game-engine", "unity", "unreal", "godot"]
- "Cybersecurity" → ["security", "cybersecurity", "cryptography", "penetration-testing"]

Expertise Level to Star Range Mapping:
- "Beginner" → Focus on well-documented projects (stars: 1000-10000)
- "Medium" → Mix of established and emerging (stars: 500-50000)
- "Advanced" → Include cutting-edge and complex projects (stars: 100-100000)

Your task:
1. Map primaryDomains to relevant topics using the mapping above
2. Use preferredLanguages to filter by 'languages' field
3. Adjust star range based on expertise level
4. Consider role: Students might prefer educational repos, Engineers prefer production-ready tools
5. Prioritize recently updated projects (pushed_at within last 2 years)

Generate a MongoDB filter query that:
- Uses $in for languages matching preferredLanguages
- Uses $in for topics matching mapped domains
- Uses $gte and $lte for star range based on expertise
- Filters for recent activity (pushed_at > "2023-01-01")
- Combines conditions with $and

Return ONLY a valid JSON object:
{{
  "filter": {{ MongoDB filter object }},
  "sort": {{ sort criteria, default by stars descending }},
  "limit": 20,
  "explanation": "Brief explanation"
}}

Output JSON:"""

        try:
            response = self.client.models.generate_content(model=self.model, contents=prompt)
            response_text = response.text.strip()

            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            query_data = json.loads(response_text)

            query_data["filter"] = _sanitize_filter(query_data.get("filter", {}))
            query_data["sort"] = _sanitize_sort(query_data.get("sort", {"stars": -1}))

            logger.info(f"Generated personalized query: {json.dumps(query_data, indent=2)}")
            return query_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            fallback_filter = {}
            if preferences.get("preferredLanguages"):
                fallback_filter["languages"] = {"$in": preferences["preferredLanguages"]}

            return {
                "filter": fallback_filter if fallback_filter else {},
                "sort": {"stars": -1},
                "limit": 20,
                "explanation": "Fallback query due to parsing error"
            }
        except Exception as e:
            logger.error(f"Error generating personalized query with Gemini: {e}")
            raise


# Global instance
gemini_generator = GeminiQueryGenerator()
