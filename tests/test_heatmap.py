def test_heatmap_requires_email(client):
    res = client.get("/api/student/heatmap")
    assert res.status_code == 400


def test_heatmap_invalid_email(client):
    res = client.get("/api/student/heatmap?email=not-an-email")
    assert res.status_code == 400


def test_heatmap_empty(client):
    res = client.get("/api/student/heatmap?email=nobody@sfedu.ru")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["by_object"] == {}
    assert data["total_tests"] == 0
    assert data["top_problematic"] == []


def test_heatmap_with_mistakes(client):
    # Сохраняем 2 теста с ошибками для тестового студента
    payload1 = {
        "email": "heatmap_test@sfedu.ru", "name": "Heat Test", "group": "G-01",
        "quiz_type": "districts", "score": 3, "max_score": 5,
        "accuracy": 60, "time_spent": "1 мин",
        "mistakes_log": ["Аксайский район", "Батайск"],
        "submission_id": "heat_sub_1"
    }
    payload2 = {
        "email": "heatmap_test@sfedu.ru", "name": "Heat Test", "group": "G-01",
        "quiz_type": "districts", "score": 2, "max_score": 5,
        "accuracy": 40, "time_spent": "1 мин",
        "mistakes_log": ["Аксайский район", "Зерноградский район"],
        "submission_id": "heat_sub_2"
    }
    client.post("/api/results/save", json=payload1)
    client.post("/api/results/save", json=payload2)

    res = client.get("/api/student/heatmap?email=heatmap_test@sfedu.ru")
    assert res.status_code == 200
    data = res.json()
    assert data["total_tests"] == 2
    assert "Аксайский район" in data["by_object"]
    assert data["by_object"]["Аксайский район"]["errors"] == 2
    assert len(data["top_problematic"]) >= 1
    assert data["top_problematic"][0]["name"] == "Аксайский район"
