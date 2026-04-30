"""Tests for services/repository.py — filter logic and DB operations."""
import pytest
from services.repository import RepositoryService


class TestBuildFilter:
    """Tests for the _build_filter private method — pure dict logic."""

    def setup_method(self):
        self.service = RepositoryService(collection=None)

    def _build(self, **kwargs):
        return self.service._build_filter(kwargs)

    def test_empty_filters(self):
        assert self._build() == {}

    def test_languages_filter(self):
        f = self._build(languages="Python,Go")
        assert f["languages"] == {"$in": ["Python", "Go"]}

    def test_languages_strips_whitespace(self):
        f = self._build(languages=" Python , Go ")
        assert "Python" in f["languages"]["$in"]
        assert "Go" in f["languages"]["$in"]

    def test_min_stars(self):
        f = self._build(min_stars=100)
        assert f["stars"]["$gte"] == 100

    def test_max_stars(self):
        f = self._build(max_stars=5000)
        assert f["stars"]["$lte"] == 5000

    def test_star_range(self):
        f = self._build(min_stars=100, max_stars=1000)
        assert f["stars"]["$gte"] == 100
        assert f["stars"]["$lte"] == 1000

    def test_min_forks(self):
        f = self._build(min_forks=10)
        assert f["forks"]["$gte"] == 10

    def test_max_forks(self):
        f = self._build(max_forks=500)
        assert f["forks"]["$lte"] == 500

    def test_fork_range(self):
        f = self._build(min_forks=10, max_forks=500)
        assert f["forks"]["$gte"] == 10
        assert f["forks"]["$lte"] == 500

    def test_has_issues(self):
        f = self._build(has_issues=True)
        assert f["issues"] == {"$gt": 0}

    def test_has_wiki(self):
        f = self._build(has_wiki=True)
        assert f["has_wiki"] is True

    def test_name_contains(self):
        f = self._build(name_contains="react")
        assert f["name"]["$regex"] == "react"
        assert f["name"]["$options"] == "i"

    def test_description_contains(self):
        f = self._build(description_contains="machine learning")
        assert f["description"]["$regex"] == "machine learning"

    def test_is_hacktoberfest(self):
        f = self._build(is_hacktoberfest=True)
        # Should add hacktoberfest to topics condition
        filter_str = str(f)
        assert "hacktoberfest" in filter_str

    def test_is_gsoc(self):
        f = self._build(is_gsoc=True)
        filter_str = str(f)
        assert "gsoc" in filter_str

    def test_hacktoberfest_and_gsoc_creates_and(self):
        f = self._build(is_hacktoberfest=True, is_gsoc=True)
        # Two topic conditions → merged with $and
        assert "$and" in f

    def test_is_underrated_sets_star_range(self):
        f = self._build(is_underrated=True)
        assert f["stars"]["$gte"] == 50
        assert f["stars"]["$lt"] == 500
        assert "pushed_at" in f

    def test_topics_filter(self):
        f = self._build(topics="machine-learning,ai")
        filter_str = str(f)
        assert "machine-learning" in filter_str

    def test_combined_language_and_stars(self):
        f = self._build(languages="Python", min_stars=1000)
        assert "languages" in f
        assert "stars" in f


class TestRepositoryServiceWithDB:
    """Integration-style tests using mongomock collection."""

    def test_get_all_repos_returns_results_and_count(self, mock_collection):
        service = RepositoryService(mock_collection)
        results, total = service.get_all_repos(page=1, limit=10)
        assert isinstance(results, list)
        assert total == 5
        assert len(results) <= 10

    def test_get_all_repos_pagination(self, mock_collection):
        service = RepositoryService(mock_collection)
        page1, total = service.get_all_repos(page=1, limit=2)
        page2, _ = service.get_all_repos(page=2, limit=2)
        assert len(page1) == 2
        assert len(page2) == 2
        # Pages should be different
        assert page1[0]["name"] != page2[0]["name"]

    def test_get_all_repos_sort_by_stars_desc(self, mock_collection):
        service = RepositoryService(mock_collection)
        results, _ = service.get_all_repos(sort_by="stars", sort_order="desc")
        stars = [r["stars"] for r in results]
        assert stars == sorted(stars, reverse=True)

    def test_get_all_repos_sort_by_stars_asc(self, mock_collection):
        service = RepositoryService(mock_collection)
        results, _ = service.get_all_repos(sort_by="stars", sort_order="asc")
        stars = [r["stars"] for r in results]
        assert stars == sorted(stars)

    def test_get_all_repos_updated_at_alias(self, mock_collection):
        """updated_at should map to pushed_at in MongoDB sort without error."""
        service = RepositoryService(mock_collection)
        results, _ = service.get_all_repos(sort_by="updated_at", sort_order="desc")
        assert isinstance(results, list)

    def test_get_all_repos_open_issues_alias(self, mock_collection):
        """open_issues should map to issues field."""
        service = RepositoryService(mock_collection)
        results, _ = service.get_all_repos(sort_by="open_issues", sort_order="desc")
        assert isinstance(results, list)

    def test_get_all_repos_language_filter(self, mock_collection):
        service = RepositoryService(mock_collection)
        results, total = service.get_all_repos(filters={"languages": "Go"})
        assert all("Go" in r.get("languages", []) for r in results)

    def test_get_all_repos_star_filter(self, mock_collection):
        service = RepositoryService(mock_collection)
        results, _ = service.get_all_repos(filters={"min_stars": 1000, "max_stars": 200000})
        for r in results:
            assert 1000 <= r["stars"] <= 200000

    def test_get_hidden_gems_returns_qualifying_repos(self, mock_collection):
        service = RepositoryService(mock_collection)
        results, total = service.get_hidden_gems(page=1, limit=20)
        # hidden-gem-tool has 500 stars — should qualify
        names = [r["name"] for r in results]
        assert "hidden-gem-tool" in names
        # pytorch (78k stars) and old-inactive (50 stars, no readme) should be excluded
        assert "pytorch" not in names
        assert "old-inactive" not in names

    def test_get_repo_found(self, mock_collection):
        service = RepositoryService(mock_collection)
        repo = service.get_repo("pytorch", "pytorch")
        assert repo is not None
        assert repo["name"] == "pytorch"
        assert "readme" in repo

    def test_get_repo_not_found(self, mock_collection):
        service = RepositoryService(mock_collection)
        repo = service.get_repo("nonexistent", "repo")
        assert repo is None

    def test_get_all_repos_empty_filters(self, mock_collection):
        service = RepositoryService(mock_collection)
        results, total = service.get_all_repos(filters={})
        assert total == 5
