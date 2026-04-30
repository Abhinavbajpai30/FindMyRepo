"""Unit tests for RecommendationService._calculate_preference_score (pure function)."""
import pytest
from services.recommendations import RecommendationService


@pytest.fixture
def service():
    return RecommendationService(collection=None)


class TestCalculatePreferenceScore:
    def test_perfect_language_match(self, service):
        repo = {"languages": ["Python"], "topics": [], "stars": 0, "pushed_at": ""}
        prefs = {"preferredLanguages": ["Python"], "primaryDomains": []}
        score = service._calculate_preference_score(repo, prefs)
        # 1.0 language match × 0.4 weight = 0.4
        assert abs(score - 0.4) < 0.01

    def test_no_language_match(self, service):
        repo = {"languages": ["Go"], "topics": [], "stars": 0, "pushed_at": ""}
        prefs = {"preferredLanguages": ["Python"], "primaryDomains": []}
        score = service._calculate_preference_score(repo, prefs)
        assert score == 0.0

    def test_partial_language_match(self, service):
        repo = {"languages": ["Python", "C++"], "topics": [], "stars": 0, "pushed_at": ""}
        prefs = {"preferredLanguages": ["Python", "Go", "Rust"], "primaryDomains": []}
        score = service._calculate_preference_score(repo, prefs)
        # 1/3 match × 0.4 = ~0.133
        assert 0.13 < score < 0.14

    def test_domain_match_adds_topic_score(self, service):
        repo = {"languages": [], "topics": ["machine-learning", "deep-learning"],
                "stars": 0, "pushed_at": ""}
        prefs = {"preferredLanguages": [], "primaryDomains": ["ML / AI / Data Science"]}
        score = service._calculate_preference_score(repo, prefs)
        assert score > 0  # topic contribution

    def test_high_stars_adds_popularity_score(self, service):
        repo = {"languages": [], "topics": [], "stars": 10000, "pushed_at": ""}
        prefs = {"preferredLanguages": [], "primaryDomains": []}
        score = service._calculate_preference_score(repo, prefs)
        assert score > 0  # popularity contribution

    def test_low_stars_no_popularity_score(self, service):
        repo = {"languages": [], "topics": [], "stars": 500, "pushed_at": ""}
        prefs = {"preferredLanguages": [], "primaryDomains": []}
        score = service._calculate_preference_score(repo, prefs)
        # stars < 1000 → no popularity weight
        assert score == 0.0

    def test_recent_push_adds_recency(self, service):
        repo = {"languages": [], "topics": [], "stars": 0, "pushed_at": "2025-01-01T00:00:00Z"}
        prefs = {"preferredLanguages": [], "primaryDomains": []}
        score = service._calculate_preference_score(repo, prefs)
        assert score == 0.1

    def test_old_push_no_recency(self, service):
        repo = {"languages": [], "topics": [], "stars": 0, "pushed_at": "2020-01-01T00:00:00Z"}
        prefs = {"preferredLanguages": [], "primaryDomains": []}
        score = service._calculate_preference_score(repo, prefs)
        assert score == 0.0

    def test_all_dimensions_combined(self, service):
        repo = {
            "languages": ["Python"],
            "topics": ["machine-learning"],
            "stars": 15000,
            "pushed_at": "2025-03-01T00:00:00Z",
        }
        prefs = {
            "preferredLanguages": ["Python"],
            "primaryDomains": ["ML / AI / Data Science"],
        }
        score = service._calculate_preference_score(repo, prefs)
        # language (0.4) + topic (>0) + popularity (0.2*min(1.5,1)=0.2) + recency (0.1)
        assert score > 0.6

    def test_no_preferences_returns_zero(self, service):
        repo = {"languages": ["Python"], "topics": ["ai"], "stars": 500, "pushed_at": ""}
        prefs = {"preferredLanguages": [], "primaryDomains": []}
        score = service._calculate_preference_score(repo, prefs)
        # No preferred languages → no language score; no domains → no topic score; stars <1000 → no popularity
        assert score == 0.0

    def test_score_does_not_exceed_reasonable_max(self, service):
        repo = {
            "languages": ["Python", "Go"],
            "topics": ["machine-learning", "deep-learning", "ai"],
            "stars": 100000,
            "pushed_at": "2026-01-01T00:00:00Z",
        }
        prefs = {
            "preferredLanguages": ["Python", "Go"],
            "primaryDomains": ["ML / AI / Data Science"],
        }
        score = service._calculate_preference_score(repo, prefs)
        # Max theoretical: 0.4 + 0.3 + 0.2 + 0.1 = 1.0
        assert score <= 1.0
