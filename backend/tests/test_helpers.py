"""Unit tests for utils/helpers.py — pure functions, no mocking needed."""
import pytest
from utils.helpers import (
    transform_repo_to_response,
    transform_repos_list,
    calculate_pagination_metadata,
)


class TestTransformRepoToResponse:
    def test_full_document(self):
        repo = {
            "name": "react",
            "owner": "facebook",
            "description": "A JS library",
            "stars": 220000,
            "forks": 45000,
            "issues": 1200,
            "languages": ["JavaScript", "TypeScript"],
            "topics": ["frontend", "ui"],
            "pushed_at": "2025-04-01T08:00:00Z",
        }
        result = transform_repo_to_response(repo)

        assert result["name"] == "react"
        assert result["full_name"] == "facebook/react"
        assert result["url"] == "https://github.com/facebook/react"
        assert result["description"] == "A JS library"
        assert result["stars"] == 220000
        assert result["forks"] == 45000
        assert result["open_issues"] == 1200
        assert result["updated_at"] == "2025-04-01T08:00:00Z"
        assert result["language"] == "JavaScript"
        assert result["languages"] == ["JavaScript", "TypeScript"]

    def test_missing_owner_falls_back_to_name_only(self):
        repo = {"name": "solo-repo", "owner": "", "description": "", "stars": 0,
                "forks": 0, "issues": 0, "languages": [], "topics": [], "pushed_at": ""}
        result = transform_repo_to_response(repo)
        assert result["full_name"] == "solo-repo"
        assert result["url"] == "https://github.com/solo-repo"

    def test_empty_languages_gives_none_primary(self):
        repo = {"name": "x", "owner": "y", "description": "", "stars": 0,
                "forks": 0, "issues": 0, "languages": [], "topics": [], "pushed_at": ""}
        result = transform_repo_to_response(repo)
        assert result["language"] is None

    def test_missing_description_defaults_to_empty_string(self):
        repo = {"name": "x", "owner": "y", "stars": 0, "forks": 0,
                "issues": 0, "languages": ["Go"], "topics": [], "pushed_at": ""}
        result = transform_repo_to_response(repo)
        assert result["description"] == ""

    def test_issues_mapped_from_issues_field(self):
        repo = {"name": "x", "owner": "y", "description": "", "stars": 0,
                "forks": 0, "issues": 42, "languages": [], "topics": [], "pushed_at": ""}
        result = transform_repo_to_response(repo)
        assert result["open_issues"] == 42

    def test_pushed_at_mapped_to_updated_at(self):
        repo = {"name": "x", "owner": "y", "description": "", "stars": 0,
                "forks": 0, "issues": 0, "languages": [], "topics": [], "pushed_at": "2024-01-01"}
        result = transform_repo_to_response(repo)
        assert result["updated_at"] == "2024-01-01"


class TestTransformReposList:
    def test_empty_list(self):
        assert transform_repos_list([]) == []

    def test_single_item(self):
        repo = {"name": "a", "owner": "b", "description": "", "stars": 1,
                "forks": 0, "issues": 0, "languages": ["Go"], "topics": [], "pushed_at": ""}
        result = transform_repos_list([repo])
        assert len(result) == 1
        assert result[0]["name"] == "a"

    def test_multiple_items(self):
        repos = [
            {"name": "a", "owner": "x", "description": "", "stars": 1,
             "forks": 0, "issues": 0, "languages": [], "topics": [], "pushed_at": ""},
            {"name": "b", "owner": "y", "description": "", "stars": 2,
             "forks": 0, "issues": 0, "languages": [], "topics": [], "pushed_at": ""},
            {"name": "c", "owner": "z", "description": "", "stars": 3,
             "forks": 0, "issues": 0, "languages": [], "topics": [], "pushed_at": ""},
        ]
        result = transform_repos_list(repos)
        assert len(result) == 3
        assert [r["name"] for r in result] == ["a", "b", "c"]


class TestCalculatePaginationMetadata:
    def test_first_page_of_many(self):
        meta = calculate_pagination_metadata(1, 20, 100, "stars", "desc")
        assert meta["current_page"] == 1
        assert meta["total_pages"] == 5
        assert meta["has_next"] is True
        assert meta["has_previous"] is False
        assert meta["next_page"] == 2
        assert meta["previous_page"] is None

    def test_last_page(self):
        meta = calculate_pagination_metadata(5, 20, 100, "stars", "desc")
        assert meta["has_next"] is False
        assert meta["has_previous"] is True
        assert meta["next_page"] is None
        assert meta["previous_page"] == 4

    def test_single_page(self):
        meta = calculate_pagination_metadata(1, 20, 10, "stars", "desc")
        assert meta["total_pages"] == 1
        assert meta["has_next"] is False
        assert meta["has_previous"] is False

    def test_ceiling_division(self):
        # 21 items / 20 per page = 2 pages
        meta = calculate_pagination_metadata(1, 20, 21, "stars", "desc")
        assert meta["total_pages"] == 2

    def test_exact_division(self):
        meta = calculate_pagination_metadata(1, 20, 40, "stars", "desc")
        assert meta["total_pages"] == 2

    def test_middle_page(self):
        meta = calculate_pagination_metadata(3, 20, 100, "name", "asc")
        assert meta["has_next"] is True
        assert meta["has_previous"] is True
        assert meta["next_page"] == 4
        assert meta["previous_page"] == 2
        assert meta["sort_by"] == "name"
        assert meta["sort_order"] == "asc"

    def test_zero_items(self):
        meta = calculate_pagination_metadata(1, 20, 0, "stars", "desc")
        assert meta["total_pages"] == 0
        assert meta["has_next"] is False
