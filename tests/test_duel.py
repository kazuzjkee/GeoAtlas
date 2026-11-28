import asyncio
import contextlib
import json
import socket
import threading
import time
import urllib.error
import urllib.request

import pytest
import uvicorn
import websockets


@contextlib.contextmanager
def _live_uvicorn():
    """Starts an isolated real Uvicorn ASGI server on an ephemeral port for WebSocket E2E tests."""
    from server import app

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", proxy_headers=True, forwarded_allow_ips="*")
    uv_server = uvicorn.Server(config)
    thread = threading.Thread(target=uv_server.run, daemon=True)
    thread.start()
    try:
        for _ in range(60):
            if uv_server.started:
                break
            time.sleep(0.05)
        assert uv_server.started
        yield port
    finally:
        uv_server.should_exit = True
        thread.join(timeout=5)


def _test_auth_header() -> dict:
    import base64
    return {"Authorization": f"Basic {base64.b64encode(b'admin:admin').decode()}"}


def _http_json(port: int, path: str, body: dict | None = None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json", "Host": f"127.0.0.1:{port}"}
    headers.update(_test_auth_header())
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        headers=headers,
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


async def _drain_until(ws, target_type: str, player_filter: str | None = None, limit: int = 40):
    for _ in range(limit):
        raw = await asyncio.wait_for(ws.recv(), timeout=8)
        msg = json.loads(raw)
        if msg.get("type") == target_type:
            if player_filter is None or msg.get("player_id") == player_filter:
                return msg
    raise AssertionError(f"Did not receive {target_type} (filter={player_filter})")


def test_duel_create_returns_unique_code_and_validates_mode(client):
    r1 = client.post("/api/duel/create", json={
        "mode": "center", "region": "rostov",
        "host_name": "Host", "host_group": "G", "host_email": "h@sfedu.ru",
    })
    r2 = client.post("/api/duel/create", json={
        "mode": "puzzle", "region": "adygey",
        "host_name": "Host2", "host_group": "G", "host_email": "h2@sfedu.ru",
    })
    assert r1.status_code == 200
    assert r2.status_code == 200
    d1, d2 = r1.json(), r2.json()
    assert d1["room_id"].startswith("DUEL-")
    assert d2["room_id"].startswith("DUEL-")
    assert d1["room_id"] != d2["room_id"]
    assert d1["mode"] == "center"
    assert d2["mode"] == "puzzle"
    assert d2["room"]["mode"] == "puzzle"
    assert d2["room"]["puzzle_anchor_id"] is not None
    assert len(d2["room"]["puzzle_piece_ids"]) >= 1
    assert "mode=puzzle" in d2["map_url"]

    bad_mode = client.post("/api/duel/create", json={
        "mode": "nonexistent_mode", "region": "rostov",
        "host_name": "Host", "host_group": "G", "host_email": "",
    })
    assert bad_mode.status_code == 400


def test_duel_join_distinct_guests_and_error_cases(client):
    created = client.post("/api/duel/create", json={
        "mode": "puzzle", "region": "rostov",
        "host_name": "Студент", "host_group": "-", "host_email": "",
    }).json()
    room_id = created["room_id"]
    host_id = created["player_id"]

    # Nonexistent room code -> 404
    missing = client.post("/api/duel/join", json={"room_id": "DUEL-0000", "player_name": "Guest"})
    assert missing.status_code == 404

    # Empty room code -> 400
    empty = client.post("/api/duel/join", json={"room_id": "   ", "player_name": "Guest"})
    assert empty.status_code == 400

    # Second unauthenticated guest with identical default name/email MUST get distinct player_id & synced total
    joined = client.post("/api/duel/join", json={
        "room_id": room_id, "player_name": "Студент", "player_group": "-", "player_email": "",
    })
    assert joined.status_code == 200
    j_data = joined.json()
    assert j_data["role"] == "join"
    assert j_data["player_id"] != host_id
    assert j_data["mode"] == "puzzle"
    players = j_data["room"]["players"]
    assert len(players) == 2
    assert players[0]["total"] == players[1]["total"] == j_data["room"]["total_items"]

    # Third player rejected when room has 2 players
    third = client.post("/api/duel/join", json={"room_id": room_id, "player_name": "Third"})
    assert third.status_code == 400

    # Surrender -> finished -> join rejected cleanly
    client.post(f"/api/duel/action/{room_id}", json={"player_id": host_id, "action": "surrender", "payload": {}})
    after_finish = client.post("/api/duel/join", json={"room_id": room_id, "player_name": "Late"})
    assert after_finish.status_code == 400


def test_duel_state(client):
    r1 = client.post("/api/duel/create", json={
        "mode": "center", "region": "rostov",
        "host_name": "H3", "host_group": "G", "host_email": "h3@sfedu.ru",
    })
    room_id = r1.json()["room_id"]
    r3 = client.get(f"/api/duel/state/{room_id}")
    assert r3.status_code == 200
    assert r3.json()["room"]["status"] in ["waiting", "ready"]


def test_duel_websocket_center_all_rounds_normal_finish():
    with _live_uvicorn() as port:
        s1, d1 = _http_json(port, "/api/duel/create", {
            "mode": "center", "region": "rostov",
            "host_name": "CenterP1", "host_group": "G1", "host_email": "c1@sfedu.ru",
        })
        assert s1 == 200
        room_id, p1_id = d1["room_id"], d1["player_id"]

        s2, d2 = _http_json(port, "/api/duel/join", {
            "room_id": room_id, "player_name": "CenterP2", "player_group": "G2", "player_email": "c2@sfedu.ru",
        })
        assert s2 == 200
        p2_id = d2["player_id"]
        assert d1["room"]["mode"] == d2["room"]["mode"] == "center"

        async def run_match():
            u1 = f"ws://127.0.0.1:{port}/ws/duel/{room_id}/{p1_id}"
            u2 = f"ws://127.0.0.1:{port}/ws/duel/{room_id}/{p2_id}"
            async with (
                websockets.connect(u1, additional_headers=_test_auth_header()) as ws1,
                websockets.connect(u2, additional_headers=_test_auth_header()) as ws2,
            ):
                await _drain_until(ws1, "player_connected", player_filter=p1_id)
                await _drain_until(ws2, "player_connected", player_filter=p2_id)

                await ws1.send(json.dumps({"type": "ping"}))
                assert (await _drain_until(ws1, "pong"))["type"] == "pong"

                await ws1.send(json.dumps({"type": "ready", "ready": True}))
                await ws2.send(json.dumps({"type": "ready", "ready": True}))

                start1 = await _drain_until(ws1, "game_start")
                start2 = await _drain_until(ws2, "game_start")
                questions = start1["room"]["questions"]
                assert len(questions) == 7
                assert questions == start2["room"]["questions"]
                assert start1["room"]["current_round"] == 0

                for r_idx, q in enumerate(questions):
                    # P1 clicks near exact coordinates -> +3 pts; P2 clicks far away -> 0 pts
                    await ws1.send(json.dumps({
                        "type": "answer_center",
                        "question_index": r_idx,
                        "lat": q["lat"],
                        "lon": q["lon"],
                        "target_name": q["name"],
                    }))
                    opp_on_2 = await _drain_until(ws2, "opponent_action", player_filter=p1_id)
                    assert opp_on_2["points"] == 3
                    assert opp_on_2["progress"] == r_idx + 1
                    assert opp_on_2["score"] == (r_idx + 1) * 3

                    await ws2.send(json.dumps({
                        "type": "answer_center",
                        "question_index": r_idx,
                        "lat": q["lat"] + 2.5,
                        "lon": q["lon"] + 2.5,
                        "target_name": q["name"],
                    }))
                    opp_on_1 = await _drain_until(ws1, "opponent_action", player_filter=p2_id)
                    assert opp_on_1["points"] == 0

                    if r_idx < len(questions) - 1:
                        rn1 = await _drain_until(ws1, "round_next")
                        rn2 = await _drain_until(ws2, "round_next")
                        assert rn1["round"] == r_idx + 1
                        assert rn2["round"] == r_idx + 1
                    else:
                        over1 = await _drain_until(ws1, "game_over")
                        over2 = await _drain_until(ws2, "game_over")
                        assert over1["room"]["status"] == "finished"
                        assert over1["room"]["finish_reason"] == "completed"
                        assert over1["room"]["winner"] == p1_id
                        assert over2["room"]["winner"] == p1_id
                        p1_final = next(p for p in over1["room"]["players"] if p["player_id"] == p1_id)
                        p2_final = next(p for p in over1["room"]["players"] if p["player_id"] == p2_id)
                        assert p1_final["score"] == 21
                        assert p1_final["correct_answers"] == 7
                        assert p2_final["score"] == 0
                        assert p2_final["mistakes"] == 7

        asyncio.run(run_match())
        _, st = _http_json(port, f"/api/duel/state/{room_id}")
        assert st["room"]["status"] == "finished"
        assert st["room"]["winner"] == p1_id


def test_duel_websocket_puzzle_mode_sync_and_finish():
    with _live_uvicorn() as port:
        _, d1 = _http_json(port, "/api/duel/create", {
            "mode": "puzzle", "region": "adygey",
            "host_name": "Puz1", "host_group": "G1", "host_email": "puz1@sfedu.ru",
        })
        room_id, p1_id = d1["room_id"], d1["player_id"]
        piece_ids = d1["room"]["puzzle_piece_ids"]
        assert len(piece_ids) >= 2

        _, d2 = _http_json(port, "/api/duel/join", {
            "room_id": room_id, "player_name": "Puz2", "player_group": "G2", "player_email": "puz2@sfedu.ru",
        })
        p2_id = d2["player_id"]
        assert d2["mode"] == "puzzle"
        assert d2["room"]["puzzle_anchor_id"] == d1["room"]["puzzle_anchor_id"]
        assert d2["room"]["puzzle_piece_ids"] == piece_ids

        async def run_puzzle():
            u1 = f"ws://127.0.0.1:{port}/ws/duel/{room_id}/{p1_id}"
            u2 = f"ws://127.0.0.1:{port}/ws/duel/{room_id}/{p2_id}"
            async with (
                websockets.connect(u1, additional_headers=_test_auth_header()) as ws1,
                websockets.connect(u2, additional_headers=_test_auth_header()) as ws2,
            ):
                await _drain_until(ws1, "player_connected", player_filter=p1_id)
                await _drain_until(ws2, "player_connected", player_filter=p2_id)

                await ws1.send(json.dumps({"type": "ready", "ready": True}))
                await ws2.send(json.dumps({"type": "ready", "ready": True}))

                start1 = await _drain_until(ws1, "game_start")
                start2 = await _drain_until(ws2, "game_start")
                assert start1["room"]["mode"] == "puzzle"
                assert start2["room"]["mode"] == "puzzle"

                await ws2.send(json.dumps({"type": "puzzle_mistake", "district_name": "Тестовый"}))
                mist_msg = await _drain_until(ws1, "opponent_action", player_filter=p2_id)
                assert mist_msg["action"] == "puzzle_mistake"
                assert mist_msg["mistakes"] == 1

                for idx, did in enumerate(piece_ids, 1):
                    await ws1.send(json.dumps({
                        "type": "place_piece",
                        "district_id": did,
                        "district_name": f"Район {idx}",
                        "placed_count": idx,
                        "mistakes": 0,
                    }))
                    opp = await _drain_until(ws2, "opponent_action", player_filter=p1_id)
                    assert opp["placed_count"] == idx
                    assert opp["score"] == idx * 10

                over1 = await _drain_until(ws1, "game_over")
                over2 = await _drain_until(ws2, "game_over")
                assert over1["room"]["status"] == "finished"
                assert over1["room"]["finish_reason"] == "completed"
                assert over1["room"]["winner"] == p1_id
                assert over2["room"]["winner"] == p1_id

        asyncio.run(run_puzzle())


@pytest.mark.parametrize("surrender_who", ["host", "join"])
def test_duel_websocket_surrender_both_sides(surrender_who):
    with _live_uvicorn() as port:
        _, d1 = _http_json(port, "/api/duel/create", {
            "mode": "center", "region": "rostov",
            "host_name": "WS Host", "host_group": "G1", "host_email": "h@sfedu.ru",
        })
        room_id, p1_id = d1["room_id"], d1["player_id"]
        _, d2 = _http_json(port, "/api/duel/join", {
            "room_id": room_id, "player_name": "WS Join", "player_group": "G2", "player_email": "j@sfedu.ru",
        })
        p2_id = d2["player_id"]

        async def run_surrender():
            u1 = f"ws://127.0.0.1:{port}/ws/duel/{room_id}/{p1_id}"
            u2 = f"ws://127.0.0.1:{port}/ws/duel/{room_id}/{p2_id}"
            async with (
                websockets.connect(u1, additional_headers=_test_auth_header()) as ws1,
                websockets.connect(u2, additional_headers=_test_auth_header()) as ws2,
            ):
                await _drain_until(ws1, "player_connected", player_filter=p1_id)
                await _drain_until(ws2, "player_connected", player_filter=p2_id)
                await ws1.send(json.dumps({"type": "ready", "ready": True}))
                await ws2.send(json.dumps({"type": "ready", "ready": True}))
                await _drain_until(ws1, "game_start")
                await _drain_until(ws2, "game_start")

                expected_winner = p2_id if surrender_who == "host" else p1_id
                sender_ws = ws1 if surrender_who == "host" else ws2
                await sender_ws.send(json.dumps({"type": "surrender"}))

                over1 = await _drain_until(ws1, "game_over")
                over2 = await _drain_until(ws2, "game_over")
                assert over1["room"]["status"] == "finished"
                assert over1["room"]["finish_reason"] == "surrender"
                assert over1["room"]["winner"] == expected_winner
                assert over2["room"]["winner"] == expected_winner

        asyncio.run(run_surrender())


def test_duel_websocket_round_timeout_and_reverse_proxy_headers():
    from server import active_duel_rooms

    with _live_uvicorn() as port:
        _, d1 = _http_json(port, "/api/duel/create", {
            "mode": "center", "region": "rostov",
            "host_name": "ProxyHost", "host_group": "G1", "host_email": "ph@sfedu.ru",
        })
        room_id, p1_id = d1["room_id"], d1["player_id"]
        _, d2 = _http_json(port, "/api/duel/join", {
            "room_id": room_id, "player_name": "ProxyJoin", "player_group": "G2", "player_email": "pj@sfedu.ru",
        })
        p2_id = d2["player_id"]

        # Shorten round duration to exercise server timeout sync deterministically
        active_duel_rooms[room_id].round_duration = 1

        # Also validate WebSocket Upgrade through a real asyncio TCP reverse proxy forwarding Upgrade/Connection/X-Forwarded-*
        async def run_proxied():
            proxy_server = await asyncio.start_server(
                lambda r, w: _pipe_proxy(r, w, port),
                "127.0.0.1",
                0,
            )
            proxy_port = proxy_server.sockets[0].getsockname()[1]
            try:
                u1 = f"ws://127.0.0.1:{proxy_port}/ws/duel/{room_id}/{p1_id}"
                u2 = f"ws://127.0.0.1:{proxy_port}/ws/duel/{room_id}/{p2_id}"
                extra_headers = {"X-Forwarded-Proto": "https", "X-Forwarded-For": "10.0.0.5", **_test_auth_header()}
                async with (
                    websockets.connect(u1, additional_headers=extra_headers) as ws1,
                    websockets.connect(u2, additional_headers=extra_headers) as ws2,
                ):
                    await _drain_until(ws1, "player_connected", player_filter=p1_id)
                    await _drain_until(ws2, "player_connected", player_filter=p2_id)
                    await ws1.send(json.dumps({"type": "ready", "ready": True}))
                    await ws2.send(json.dumps({"type": "ready", "ready": True}))
                    await _drain_until(ws1, "game_start")
                    await _drain_until(ws2, "game_start")

                    # Wait for round 0 timeout -> both receive round_next simultaneously without answering
                    rn1 = await _drain_until(ws1, "round_next")
                    rn2 = await _drain_until(ws2, "round_next")
                    assert rn1["round"] == 1
                    assert rn2["round"] == 1

                    await ws1.send(json.dumps({"type": "surrender"}))
                    over = await _drain_until(ws2, "game_over")
                    assert over["room"]["winner"] == p2_id
            finally:
                proxy_server.close()
                await proxy_server.wait_closed()

        asyncio.run(run_proxied())


async def _pipe_proxy(client_reader, client_writer, target_port: int):
    upstream_reader, upstream_writer = await asyncio.open_connection("127.0.0.1", target_port)

    async def forward(src, dst):
        try:
            while True:
                chunk = await src.read(4096)
                if not chunk:
                    break
                dst.write(chunk)
                await dst.drain()
        except Exception:
            pass
        finally:
            try:
                dst.close()
            except Exception:
                pass

    await asyncio.gather(
        forward(client_reader, upstream_writer),
        forward(upstream_reader, client_writer),
        return_exceptions=True,
    )


def test_duel_http_polling_full_lifecycle(client):
    c = client.post("/api/duel/create", json={
        "mode": "center", "region": "rostov",
        "host_name": "PollHost", "host_group": "G-1", "host_email": "ph@sfedu.ru",
    })
    assert c.status_code == 200
    cd = c.json()
    rid, p1_id = cd["room_id"], cd["player_id"]

    j = client.post("/api/duel/join", json={
        "room_id": rid,
        "player_name": "PollGuest", "player_group": "G-1", "player_email": "pg@sfedu.ru",
    })
    assert j.status_code == 200
    p2_id = j.json()["player_id"]

    r1 = client.post(f"/api/duel/action/{rid}", json={"player_id": p1_id, "action": "ready", "payload": {"ready": True}})
    r2 = client.post(f"/api/duel/action/{rid}", json={"player_id": p2_id, "action": "ready", "payload": {"ready": True}})
    assert r1.status_code == 200 and r2.status_code == 200

    st = client.get(f"/api/duel/state/{rid}")
    assert st.status_code == 200
    assert st.json()["room"]["status"] == "playing"

    sur = client.post(f"/api/duel/action/{rid}", json={"player_id": p2_id, "action": "surrender", "payload": {}})
    assert sur.status_code == 200
    st_end = client.get(f"/api/duel/state/{rid}")
    assert st_end.status_code == 200
    assert st_end.json()["room"]["status"] == "finished"
