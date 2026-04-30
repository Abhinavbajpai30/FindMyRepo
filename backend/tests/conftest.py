"""Shared fixtures for all backend tests."""
import sys
import os
import pytest
import mongomock

# Make sure backend/ is on the path so imports like `from utils.helpers import ...` work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


SAMPLE_REPOS = [
    {
        "name": "pytorch",
        "owner": "pytorch",
        "description": "Tensors and Dynamic neural networks in Python",
        "stars": 78000,
        "forks": 20000,
        "issues": 12000,
        "languages": ["Python", "C++"],
        "topics": ["machine-learning", "deep-learning", "ai", "neural-networks"],
        "pushed_at": "2025-03-15T10:00:00Z",
        "has_wiki": True,
        "readme": "PyTorch is an open source machine learning framework.",
        "embedding": [0.1] * 384,
    },
    {
        "name": "react",
        "owner": "facebook",
        "description": "A declarative JavaScript library for building user interfaces",
        "stars": 220000,
        "forks": 45000,
        "issues": 1200,
        "languages": ["JavaScript", "TypeScript"],
        "topics": ["frontend", "web", "ui", "react"],
        "pushed_at": "2025-04-01T08:00:00Z",
        "has_wiki": False,
        "readme": "React is a JavaScript library for building UIs.",
        "embedding": [0.2] * 384,
    },
    {
        "name": "kubernetes",
        "owner": "kubernetes",
        "description": "Production-Grade Container Scheduling and Management",
        "stars": 108000,
        "forks": 38000,
        "issues": 2500,
        "languages": ["Go"],
        "topics": ["devops", "kubernetes", "docker", "infrastructure"],
        "pushed_at": "2024-06-10T12:00:00Z",
        "has_wiki": True,
        "readme": "Kubernetes is an open-source container orchestration system.",
        "embedding": [0.3] * 384,
    },
    {
        "name": "hidden-gem-tool",
        "owner": "indie-dev",
        "description": "A niche developer tool with moderate stars",
        "stars": 500,
        "forks": 40,
        "issues": 10,
        "languages": ["Rust"],
        "topics": ["cli", "tool"],
        "pushed_at": "2025-01-20T09:00:00Z",
        "has_wiki": False,
        "readme": "A handy CLI tool for developers.",
        "embedding": [0.4] * 384,
    },
    {
        "name": "old-inactive",
        "owner": "someone",
        "description": "Archived project nobody uses",
        "stars": 50,
        "forks": 5,
        "issues": 0,
        "languages": ["PHP"],
        "topics": [],
        "pushed_at": "2019-01-01T00:00:00Z",
        "has_wiki": False,
        "readme": None,
        "embedding": [0.5] * 384,
    },
]


@pytest.fixture
def mock_collection():
    """In-memory MongoDB collection populated with sample repos."""
    client = mongomock.MongoClient()
    db = client["findmyrepo"]
    col = db["repos"]
    col.insert_many([r.copy() for r in SAMPLE_REPOS])
    return col


@pytest.fixture
def sample_repo():
    return SAMPLE_REPOS[0].copy()
