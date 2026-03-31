"""
Shared pytest fixtures for b0bot test suite.

All external dependencies (Pinecone, SentenceTransformers, HuggingFace,
LangChain) are stubbed here so tests run without API keys, GPU, or
network access.

Design note — why sys.modules injection instead of patch():
  mock.patch("some.module.Class") requires the module to already be
  importable. When sentence_transformers / langchain_community are not
  installed, patch() itself raises ModuleNotFoundError before the test
  body runs. The correct approach for uninstalled packages is to inject
  a MagicMock into sys.modules BEFORE any project code imports them.
"""
import sys
import os
import types
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

# ── Ensure project root is on sys.path ──────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── Pre-inject stubs for packages that may not be installed ─────────────────
# This must happen at module level (before any test collection imports
# project code) — conftest.py is loaded by pytest before test files.

def _stub_module(name: str) -> MagicMock:
    """Create a MagicMock and register it under `name` in sys.modules."""
    mod = MagicMock(name=name)
    sys.modules[name] = mod
    return mod


# sentence_transformers ── only inject if not already installed
if "sentence_transformers" not in sys.modules:
    _st = _stub_module("sentence_transformers")
    _dense_stub = MagicMock()
    _dense_stub.encode.return_value = np.zeros(384, dtype="float32")
    _sparse_stub = MagicMock()
    _sparse_stub.encode.return_value = np.array([0.0, 0.5] + [0.0] * 382)
    _st.SentenceTransformer.return_value = _dense_stub
    _st.SparseEncoder.return_value = _sparse_stub

# langchain_community.llms — stub only the HuggingFaceEndpoint
if "langchain_community" not in sys.modules:
    _lc = types.ModuleType("langchain_community")
    _lc_llms = types.ModuleType("langchain_community.llms")
    _lc_llms.HuggingFaceEndpoint = MagicMock(name="HuggingFaceEndpoint")
    _lc.llms = _lc_llms
    sys.modules["langchain_community"] = _lc
    sys.modules["langchain_community.llms"] = _lc_llms


# ── Pinecone mock helpers ────────────────────────────────────────────────────

SAMPLE_METADATA = {
    "headlines": "Critical CVE-2025-9999 found in OpenSSL",
    "author": "CISA",
    "fullNews": "A critical remote code execution vulnerability was disclosed...",
    "newsURL": "https://cisa.gov/known-exploited-vulnerabilities/cve-2025-9999",
    "newsImgURL": "https://cisa.gov/img/cve.png",
    "newsDate": "Jan 01, 2025",
}

SAMPLE_ARTICLE = {
    "id": 20250101,
    "headlines": SAMPLE_METADATA["headlines"],
    "author":    SAMPLE_METADATA["author"],
    "fullNews":  SAMPLE_METADATA["fullNews"],
    "newsURL":   SAMPLE_METADATA["newsURL"],
    "newsImgURL": SAMPLE_METADATA["newsImgURL"],
    "newsDate":  SAMPLE_METADATA["newsDate"],
}


def _make_pinecone_index_stub():
    """Return a MagicMock for pinecone.Index with list/fetch/query/upsert."""
    index = MagicMock()

    # index.list() → generator yielding one page of IDs
    index.list.return_value = iter([["vec-001"]])

    # index.fetch() → object with .vectors dict
    fetch_result = MagicMock()
    vec = MagicMock()
    vec.metadata = SAMPLE_METADATA.copy()
    fetch_result.vectors = {"vec-001": vec}
    index.fetch.return_value = fetch_result

    # index.query() → object with .matches list
    query_result = MagicMock()
    match = MagicMock()
    match.metadata = SAMPLE_METADATA.copy()
    match.score = 0.95
    query_result.matches = [match]
    index.query.return_value = query_result

    # index.upsert() → no-op
    index.upsert.return_value = None

    return index


def _make_pinecone_client_stub(index_stub):
    """Return a MagicMock for the top-level Pinecone client."""
    pc = MagicMock()
    pc.Index.return_value = index_stub
    pc.list_indexes.return_value.names.return_value = []
    return pc


# ── Session-scoped fixtures (created once per test session) ─────────────────

@pytest.fixture(scope="session")
def mock_index():
    """A reusable stub for a Pinecone Index."""
    return _make_pinecone_index_stub()


@pytest.fixture(scope="session")
def mock_pinecone_client(mock_index):
    """A reusable stub for the Pinecone top-level client."""
    return _make_pinecone_client_stub(mock_index)


# ── Function-scoped Flask app fixture ────────────────────────────────────────

@pytest.fixture()
def flask_app(mock_pinecone_client):
    """
    A Flask test application with all external dependencies mocked.

    sentence_transformers and langchain_community are already stubbed via
    sys.modules injection at module load time (see top of this file).
    Only pinecone.Pinecone needs a runtime patch since it IS installed but
    we want to intercept the client constructor to avoid real API calls.
    """
    with patch("pinecone.Pinecone", return_value=mock_pinecone_client):
        # Import after patch so config.Database.py sees the mock client
        from app import app as flask_application
        flask_application.config.update({
            "TESTING":    True,
            "SECRET_KEY": "test-secret",
        })
        yield flask_application


@pytest.fixture()
def client(flask_app):
    """A Flask test client bound to the mocked application."""
    with flask_app.test_client() as c:
        yield c


# ── Standalone NewsService fixture (no Flask context needed) ─────────────────

@pytest.fixture()
def news_service_raw(mock_pinecone_client):
    """
    A NewsService(model_name=None) instance with Pinecone mocked.
    Use this to test service-layer logic in isolation.
    """
    with patch("pinecone.Pinecone", return_value=mock_pinecone_client):
        from services.NewsService import NewsService
        return NewsService(model_name=None)
