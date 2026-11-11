def test_save_result_ok(client):
    payload = {
        "email": "s@sfedu.ru", "name": "Студент", "group": "G-01",
        "quiz_type": "districts", "score": 8, "max_score": 10,
        "accuracy": 80, "time_spent": "1 мин", "is_exam": False,
        "submission_id": "test_sub_1"
    }
    res = client.post("/api/results/save", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_save_result_dedup(client):
    payload = {
        "email": "s2@sfedu.ru", "name": "S2", "group": "G-01",
        "quiz_type": "districts", "score": 5, "max_score": 10,
        "accuracy": 50, "time_spent": "1 мин", "is_exam": False,
        "submission_id": "test_sub_dup"
    }
    client.post("/api/results/save", json=payload)
    payload["score"] = 9
    payload["accuracy"] = 90
    res = client.post("/api/results/save", json=payload)
    assert res.status_code == 200

def test_leaderboard(client):
    res = client.get("/api/results/leaderboard")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
