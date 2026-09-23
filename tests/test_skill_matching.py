# tests/test_skill_matching.py
import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.model_registry import load_models

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_models():
    load_models()


def test_skill_matching_success():
    payload = {
        "candidate_id": "kandidat-123",
        "job_id": "lowongan-456",
        "resume_text": "Pengalaman 3 tahun sebagai Full Stack Web Developer dengan Laravel, PHP, REST API, MySQL, dan Vue.js.",
        "job_description": "Dibutuhkan Backend Engineer yang menguasai Laravel, PHP, Database MySQL, dan arsitektur API.",
        "required_skills": ["Laravel", "PHP", "MySQL", "Docker"],
        "candidate_skills": ["Laravel", "PHP", "MySQL", "Vue.js"],
    }
    response = client.post("/api/v1/skill-matching", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["status"] == "completed"
    assert data["similarity_score"] > 50.0
    assert data["cosine_similarity"] > 0.5
    assert len(data["matched_skills"]) >= 2
    matched_names = [s["skill"] for s in data["matched_skills"]]
    assert "Laravel" in matched_names
    assert "PHP" in matched_names
    assert data["skill_coverage"] is not None


def test_skill_matching_empty_input():
    payload = {
        "candidate_id": "kandidat-empty",
        "job_id": "lowongan-empty",
        "resume_text": "   ",
        "job_description": "Deskripsi pekerjaan",
    }
    response = client.post("/api/v1/skill-matching", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["similarity_score"] == 0.0
