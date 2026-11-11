def test_send_code_ok(client):
    res = client.post("/api/auth/send-code", json={
        "email": "test@sfedu.ru", "full_name": "Test", "group_num": "G-01"
    })
    assert res.status_code == 200
    assert "dev_code" in res.json()

def test_send_code_wrong_domain(client):
    res = client.post("/api/auth/send-code", json={
        "email": "test@gmail.com", "full_name": "Test", "group_num": "G-01"
    })
    assert res.status_code == 400

def test_verify_code_ok(client):
    r1 = client.post("/api/auth/send-code", json={
        "email": "t2@sfedu.ru", "full_name": "T2", "group_num": "G-02"
    })
    code = r1.json()["dev_code"]
    r2 = client.post("/api/auth/verify-code", json={"email": "t2@sfedu.ru", "code": code})
    assert r2.status_code == 200
    assert r2.json()["user"]["email"] == "t2@sfedu.ru"

def test_verify_code_wrong(client):
    res = client.post("/api/auth/verify-code", json={"email": "x@sfedu.ru", "code": "000000"})
    assert res.status_code == 400
