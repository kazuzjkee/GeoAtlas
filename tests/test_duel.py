def test_duel_create(client):
    res = client.post("/api/duel/create", json={
        "mode": "center", "region": "rostov",
        "host_name": "Host", "host_group": "G", "host_email": "h@sfedu.ru"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["room_id"].startswith("DUEL-")
    assert data["player_id"]

def test_duel_join(client):
    r1 = client.post("/api/duel/create", json={
        "mode": "center", "region": "rostov",
        "host_name": "H2", "host_group": "G", "host_email": "h2@sfedu.ru"
    })
    room_id = r1.json()["room_id"]
    r2 = client.post("/api/duel/join", json={
        "room_id": room_id, "player_name": "J2", "player_group": "G", "player_email": "j2@sfedu.ru"
    })
    assert r2.status_code == 200
    assert r2.json()["role"] == "join"

def test_duel_state(client):
    r1 = client.post("/api/duel/create", json={
        "mode": "center", "region": "rostov",
        "host_name": "H3", "host_group": "G", "host_email": "h3@sfedu.ru"
    })
    room_id = r1.json()["room_id"]
    r3 = client.get(f"/api/duel/state/{room_id}")
    assert r3.status_code == 200
    assert r3.json()["room"]["status"] in ["waiting", "ready"]
