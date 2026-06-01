"""Интеграционный тест HTTP API: полный пайплайн подменяется mock."""
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api_service import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "running"


def test_analyze_video_rejects_non_video(client):
    r = client.post(
        "/analyze-video",
        files={"file": ("x.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 200
    body = r.json()
    assert "error" in body


@patch("api_service.SkiAnalysisPipeline")
def test_analyze_video_mock_pipeline(MockPipeline, client):
    inst = MagicMock()
    inst.analyze_user_video.return_value = {
        "analysis": {"overall_score": 72.5, "angle_analysis": []},
        "files": {"resampled": "/tmp/x.csv"},
    }
    MockPipeline.return_value = inst

    r = client.post(
        "/analyze-video",
        files={"file": ("clip.mp4", BytesIO(b"dummy-bytes"), "video/mp4")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "analysis" in data
    assert data["analysis"]["overall_score"] == 72.5
    inst.analyze_user_video.assert_called_once()
