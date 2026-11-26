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


def test_duel_websocket_two_players_and_finish(client):
    import asyncio
    import json
    import socket
    import threading
    import time
    import urllib.request
    import uvicorn
    import websockets
    from server import app

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    uv_server = uvicorn.Server(config)
    t = threading.Thread(target=uv_server.run, daemon=True)
    t.start()

    try:
        for _ in range(50):
            if uv_server.started:
                break
            time.sleep(0.05)
        assert uv_server.started

        def post_json(path, body):
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}{path}",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json", "Host": f"127.0.0.1:{port}"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))

        s1, d1 = post_json("/api/duel/create", {
            "mode": "center", "region": "rostov",
            "host_name": "WS Host", "host_group": "G1", "host_email": "wshost@sfedu.ru"
        })
        assert s1 == 200
        room_id, p1_id = d1["room_id"], d1["player_id"]

        s2, d2 = post_json("/api/duel/join", {
            "room_id": room_id, "player_name": "WS Join", "player_group": "G2", "player_email": "wsjoin@sfedu.ru"
        })
        assert s2 == 200
        p2_id = d2["player_id"]

        async def run_duel():
            u1 = f"ws://127.0.0.1:{port}/ws/duel/{room_id}/{p1_id}"
            u2 = f"ws://127.0.0.1:{port}/ws/duel/{room_id}/{p2_id}"
            async with websockets.connect(u1) as ws1, websockets.connect(u2) as ws2:
                async def drain_until(ws, target_type, player_filter=None):
                    for _ in range(25):
                        m = json.loads(await asyncio.wait_for(ws.recv(), timeout=6))
                        if m.get("type") == target_type:
                            if player_filter is None or m.get("player_id") == player_filter:
                                return m
                    raise AssertionError(f"Did not receive {target_type}")

                p1_conn = await drain_until(ws1, "player_connected", player_filter=p1_id)
                p2_conn = await drain_until(ws2, "player_connected", player_filter=p2_id)
                assert p1_conn["player_id"] == p1_id
                assert p2_conn["player_id"] == p2_id

                await ws1.send(json.dumps({"type": "ping"}))
                pong = await drain_until(ws1, "pong")
                assert pong["type"] == "pong"

                await ws1.send(json.dumps({"type": "ready", "ready": True}))
                await ws2.send(json.dumps({"type": "ready", "ready": True}))

                start1 = await drain_until(ws1, "game_start")
                start2 = await drain_until(ws2, "game_start")
                assert start1["room"]["status"] == "playing"
                assert start2["room"]["status"] == "playing"

                await ws1.send(json.dumps({
                    "type": "answer_center", "points": 3, "distance": 12.5, "question_index": 0, "target_name": "Ростов"
                }))
                opp_msg = await drain_until(ws2, "opponent_action", player_filter=p1_id)
                assert opp_msg["score"] == 3
                assert opp_msg["progress"] == 1

                await ws2.send(json.dumps({"type": "surrender"}))
                over1 = await drain_until(ws1, "game_over")
                over2 = await drain_until(ws2, "game_over")
                assert over1["room"]["status"] == "finished"
                assert over1["room"]["winner"] == p1_id
                assert over2["room"]["winner"] == p1_id

        asyncio.run(run_duel())

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/duel/state/{room_id}", timeout=5) as r:
            assert r.status == 200
            st = json.loads(r.read().decode("utf-8"))
            assert st["room"]["status"] == "finished"
            assert st["room"]["winner"] == p1_id
    finally:
        uv_server.should_exit = True
        t.join(timeout=5)
