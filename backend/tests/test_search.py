"""Tests for services/search.py — verifies $vectorSearch pipeline construction."""
import pytest
from unittest.mock import MagicMock, patch


class TestSearchService:
    def _make_service(self, aggregate_return=None):
        """Return a SearchService with a mocked collection."""
        from services.search import SearchService
        col = MagicMock()
        col.aggregate.return_value = aggregate_return or []
        return SearchService(col)

    def _fake_embedding(self):
        return [0.1] * 384

    def test_search_calls_aggregate(self):
        service = self._make_service()
        with patch("services.search.embedding_generator.generate", return_value=self._fake_embedding()):
            service.search("machine learning", limit=10)
        service.collection.aggregate.assert_called_once()

    def test_search_pipeline_has_vector_search_stage(self):
        service = self._make_service()
        with patch("services.search.embedding_generator.generate", return_value=self._fake_embedding()):
            service.search("python", limit=20)
        pipeline = service.collection.aggregate.call_args[0][0]
        assert pipeline[0].get("$vectorSearch") is not None

    def test_search_uses_correct_index_name(self):
        service = self._make_service()
        with patch("services.search.embedding_generator.generate", return_value=self._fake_embedding()):
            service.search("python", limit=20)
        pipeline = service.collection.aggregate.call_args[0][0]
        vs = pipeline[0]["$vectorSearch"]
        assert vs["index"] == "embedding_vector_index"

    def test_search_uses_correct_path(self):
        service = self._make_service()
        with patch("services.search.embedding_generator.generate", return_value=self._fake_embedding()):
            service.search("python", limit=20)
        pipeline = service.collection.aggregate.call_args[0][0]
        vs = pipeline[0]["$vectorSearch"]
        assert vs["path"] == "embedding"

    def test_search_num_candidates_is_ten_times_limit(self):
        service = self._make_service()
        with patch("services.search.embedding_generator.generate", return_value=self._fake_embedding()):
            service.search("python", limit=30)
        pipeline = service.collection.aggregate.call_args[0][0]
        vs = pipeline[0]["$vectorSearch"]
        assert vs["numCandidates"] == 300
        assert vs["limit"] == 30

    def test_search_passes_query_vector(self):
        embedding = [0.42] * 384
        service = self._make_service()
        with patch("services.search.embedding_generator.generate", return_value=embedding):
            service.search("test query", limit=10)
        pipeline = service.collection.aggregate.call_args[0][0]
        vs = pipeline[0]["$vectorSearch"]
        assert vs["queryVector"] == embedding

    def test_search_pipeline_adds_similarity_score_field(self):
        service = self._make_service()
        with patch("services.search.embedding_generator.generate", return_value=self._fake_embedding()):
            service.search("python", limit=10)
        pipeline = service.collection.aggregate.call_args[0][0]
        add_fields = pipeline[1].get("$addFields", {})
        assert "similarity_score" in add_fields

    def test_search_returns_aggregate_results(self):
        fake_results = [
            {"name": "pytorch", "owner": "pytorch", "similarity_score": 0.95},
            {"name": "tensorflow", "owner": "google", "similarity_score": 0.88},
        ]
        service = self._make_service(aggregate_return=iter(fake_results))
        with patch("services.search.embedding_generator.generate", return_value=self._fake_embedding()):
            results = service.search("deep learning", limit=60)
        assert len(results) == 2
        assert results[0]["name"] == "pytorch"

    def test_search_propagates_embedding_exception(self):
        from services.search import SearchService
        service = SearchService(MagicMock())
        with patch("services.search.embedding_generator.generate", side_effect=RuntimeError("model error")):
            with pytest.raises(RuntimeError, match="model error"):
                service.search("python")

    def test_search_default_limit_is_60(self):
        service = self._make_service()
        with patch("services.search.embedding_generator.generate", return_value=self._fake_embedding()):
            service.search("python")
        pipeline = service.collection.aggregate.call_args[0][0]
        assert pipeline[0]["$vectorSearch"]["limit"] == 60
