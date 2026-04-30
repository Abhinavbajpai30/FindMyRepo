"""Integration tests for all FastAPI endpoints using TestClient."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ── helpers ─────────────────────────────────────────────────────────────────

def _make_repo(**overrides):
    base = {
        "name": "pytorch", "owner": "pytorch",
        "description": "ML framework", "stars": 78000, "forks": 20000,
        "issues": 500, "languages": ["Python"], "topics": ["machine-learning"],
        "pushed_at": "2025-01-01T00:00:00Z",
    }
    base.update(overrides)
    return base


def _make_app(
    search_results=None,
    all_repos_result=None,
    hidden_gems_result=None,
    single_repo=None,
    recommendation_results=None,
):
    """Build a test FastAPI app with all external dependencies mocked out."""

    # Patch heavy imports before main.py is loaded
    with (
        patch("utils.embeddings.SentenceTransformer"),
        patch("utils.gemini_service.genai"),
    ):
        import main as app_module

    mock_search = MagicMock()
    mock_search.search.return_value = search_results or [_make_repo()]

    repos = all_repos_result or ([_make_repo()], 1)
    mock_repo = MagicMock()
    mock_repo.get_all_repos.return_value = repos
    mock_repo.get_hidden_gems.return_value = hidden_gems_result or ([_make_repo()], 1)
    mock_repo.get_repo.return_value = single_repo  # None = 404

    mock_rec = MagicMock()
    mock_rec.get_personalized_repos.return_value = recommendation_results or [_make_repo()]

    mock_db = MagicMock()
    mock_db.get_collection.return_value = MagicMock(estimated_document_count=MagicMock(return_value=43000))

    app_module.search_service = mock_search
    app_module.repository_service = mock_repo
    app_module.recommendation_service = mock_rec
    app_module.db_instance = mock_db

    return TestClient(app_module.app)


@pytest.fixture
def client():
    return _make_app()


# ── GET / ────────────────────────────────────────────────────────────────────

class TestRoot:
    def test_returns_ok(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "version" in data

# ── GET /health ───────────────────────────────────────────────────────────────

class TestHealth:
    def test_healthy(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "repositories_count" in data

# ── POST /search ──────────────────────────────────────────────────────────────

class TestSearch:
    def test_valid_query(self, client):
        r = client.post("/search", json={"query": "python machine learning"})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert isinstance(data["results"], list)
        assert "total_returned" in data

    def test_default_limit_accepted(self, client):
        r = client.post("/search", json={"query": "python"})
        assert r.status_code == 200

    def test_custom_limit(self, client):
        r = client.post("/search", json={"query": "python", "limit": 30})
        assert r.status_code == 200

    def test_limit_below_minimum_rejected(self, client):
        r = client.post("/search", json={"query": "python", "limit": 5})
        assert r.status_code == 422

    def test_limit_above_maximum_rejected(self, client):
        r = client.post("/search", json={"query": "python", "limit": 200})
        assert r.status_code == 422

    def test_empty_query_rejected(self, client):
        r = client.post("/search", json={"query": ""})
        assert r.status_code == 422

    def test_missing_query_rejected(self, client):
        r = client.post("/search", json={})
        assert r.status_code == 422

    def test_service_unavailable(self):
        with (
            patch("utils.embeddings.SentenceTransformer"),
            patch("utils.gemini_service.genai"),
        ):
            import main as app_module
        app_module.search_service = None
        c = TestClient(app_module.app)
        r = c.post("/search", json={"query": "python"})
        assert r.status_code == 503

# ── POST /userpreferences ─────────────────────────────────────────────────────

class TestUserPreferences:
    VALID_PREFS = {
        "primaryDomains": ["ML / AI / Data Science"],
        "role": "Engineer",
        "expertise": "Advanced",
        "preferredLanguages": ["Python"],
    }

    def test_valid_preferences(self, client):
        r = client.post("/userpreferences", json=self.VALID_PREFS)
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert isinstance(data["results"], list)

    def test_missing_role_rejected(self, client):
        prefs = {k: v for k, v in self.VALID_PREFS.items() if k != "role"}
        r = client.post("/userpreferences", json=prefs)
        assert r.status_code == 422

    def test_missing_expertise_rejected(self, client):
        prefs = {k: v for k, v in self.VALID_PREFS.items() if k != "expertise"}
        r = client.post("/userpreferences", json=prefs)
        assert r.status_code == 422

    def test_service_unavailable(self):
        with (
            patch("utils.embeddings.SentenceTransformer"),
            patch("utils.gemini_service.genai"),
        ):
            import main as app_module
        app_module.recommendation_service = None
        c = TestClient(app_module.app)
        r = c.post("/userpreferences", json=self.VALID_PREFS)
        assert r.status_code == 503

# ── GET /allrepos ─────────────────────────────────────────────────────────────

class TestAllRepos:
    def test_default_params(self, client):
        r = client.get("/allrepos")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data

    def test_valid_sort_by_stars(self, client):
        r = client.get("/allrepos?sort_by=stars&sort_order=desc")
        assert r.status_code == 200

    def test_valid_sort_by_updated_at(self, client):
        r = client.get("/allrepos?sort_by=updated_at")
        assert r.status_code == 200

    def test_valid_sort_by_open_issues(self, client):
        r = client.get("/allrepos?sort_by=open_issues")
        assert r.status_code == 200

    def test_invalid_sort_by_returns_400(self, client):
        r = client.get("/allrepos?sort_by=invalid_field")
        assert r.status_code == 400

    def test_invalid_sort_order_returns_422(self, client):
        r = client.get("/allrepos?sort_order=sideways")
        assert r.status_code == 422

    def test_page_zero_rejected(self, client):
        r = client.get("/allrepos?page=0")
        assert r.status_code == 422

    def test_limit_above_100_rejected(self, client):
        r = client.get("/allrepos?limit=101")
        assert r.status_code == 422

    def test_filter_params_accepted(self, client):
        r = client.get("/allrepos?min_stars=100&languages=Python&has_issues=true")
        assert r.status_code == 200

    def test_filters_applied_in_response(self, client):
        r = client.get("/allrepos?min_stars=100")
        assert r.status_code == 200
        data = r.json()
        assert "filters_applied" in data

    def test_pagination_metadata_present(self, client):
        r = client.get("/allrepos")
        pagination = r.json()["pagination"]
        for key in ("current_page", "total_pages", "has_next", "has_previous", "total_items"):
            assert key in pagination

# ── GET /hiddengem ────────────────────────────────────────────────────────────

class TestHiddenGem:
    def test_default_params(self, client):
        r = client.get("/hiddengem")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data

    def test_invalid_sort_by_returns_400(self, client):
        r = client.get("/hiddengem?sort_by=badfield")
        assert r.status_code == 400

    def test_valid_sort_options(self, client):
        for field in ("stars", "forks", "updated_at", "open_issues", "name"):
            r = client.get(f"/hiddengem?sort_by={field}")
            assert r.status_code == 200, f"Failed for sort_by={field}"

# ── GET /repo/{owner}/{name} ──────────────────────────────────────────────────

class TestRepoDetail:
    def test_existing_repo(self):
        repo = {**_make_repo(), "readme": "# PyTorch\nA great ML library."}
        client = _make_app(single_repo=repo)
        r = client.get("/repo/pytorch/pytorch")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "pytorch"
        assert "readme" in data

    def test_nonexistent_repo_returns_404(self):
        client = _make_app(single_repo=None)
        r = client.get("/repo/nobody/nothing")
        assert r.status_code == 404

    def test_readme_can_be_null(self):
        repo = {**_make_repo(), "readme": None}
        client = _make_app(single_repo=repo)
        r = client.get("/repo/pytorch/pytorch")
        assert r.status_code == 200
