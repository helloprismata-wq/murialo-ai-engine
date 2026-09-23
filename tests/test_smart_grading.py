# tests/test_smart_grading.py
import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.model_registry import load_models

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_models():
    load_models()


def test_smart_grading_single_high_score():
    payload = {
        "candidate_id": "cand-001",
        "question_id": "soal-01",
        "candidate_answer": "Dependency injection adalah teknik perancangan di mana dependensi objek disuntikkan dari luar daripada dibuat di dalam kelas tersebut.",
        "reference_answers": [
            "Dependency injection merupakan pola desain di mana suatu objek menerima dependensi dari entitas luar untuk meningkatkan modularitas dan pengujian."
        ],
        "max_score": 10.0,
    }
    response = client.post("/api/v1/smart-grading", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["status"] == "completed"
    assert data["cosine_similarity"] > 0.7
    assert data["predicted_score"] >= 7.0
    assert data["max_score"] == 10.0


def test_smart_grading_blank_answer():
    payload = {
        "candidate_id": "cand-002",
        "question_id": "soal-02",
        "candidate_answer": "",
        "reference_answers": ["Jawaban acuan resmi."],
        "max_score": 10.0,
    }
    response = client.post("/api/v1/smart-grading", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "completed"
    assert data["predicted_score"] == 0.0


def test_smart_grading_batch():
    payload = {
        "items": [
            {
                "candidate_id": "cand-001",
                "question_id": "soal-01",
                "candidate_answer": "REST API menggunakan metode HTTP seperti GET, POST, PUT, DELETE untuk manipulasi data stateless.",
                "reference_answers": ["REST API adalah arsitektur layanan web berbasis HTTP dengan operasi stateless."],
                "max_score": 10.0,
            },
            {
                "candidate_id": "cand-001",
                "question_id": "soal-02",
                "candidate_answer": "Saya tidak tahu jawabannya.",
                "reference_answers": ["Penjelasan mendalam tentang ACID compliance pada database relasional."],
                "max_score": 15.0,
            }
        ]
    }
    response = client.post("/api/v1/smart-grading/batch", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["total"] == 2
    assert res_data["completed"] == 2
    assert len(res_data["data"]) == 2
