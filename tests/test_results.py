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

def test_save_result_csrf_blocked(client):
    payload = {
        "email": "s_csrf@sfedu.ru", "name": "Evil", "group": "G-01",
        "quiz_type": "districts", "score": 8, "max_score": 10,
        "accuracy": 80, "time_spent": "1 мин", "is_exam": False,
        "submission_id": "test_sub_csrf"
    }
    res = client.post("/api/results/save", json=payload, headers={"Origin": "https://evil.com", "Host": "testserver"})
    assert res.status_code == 403

def test_student_dashboard_ok(client):
    res = client.get("/api/student/dashboard?email=s@sfedu.ru")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "stats" in data
    assert "regions" in data

def test_save_result_adaptive(client):
    payload = {
        "email": "adapt@sfedu.ru", "name": "Адаптивный", "group": "G-01",
        "quiz_type": "districts", "score": 9, "max_score": 10,
        "accuracy": 90, "time_spent": "1 мин", "is_exam": False,
        "is_adaptive": True,
        "submission_id": "test_sub_adaptive"
    }
    res = client.post("/api/results/save", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    import db
    results = db.load_results()
    saved = next((r for r in results if r["submission_id"] == "test_sub_adaptive"), None)
    assert saved is not None
    assert saved["is_adaptive"] is True
