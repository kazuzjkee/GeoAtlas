import os
import db
import server


def test_russia_map_disabled_by_default_and_preserved_on_disk():
    assert server.RUSSIA_MAP_ENABLED is False
    assert os.path.exists(os.path.join(server.MAPS_DIR, "russia_quiz_map.html"))
    assert os.path.exists(os.path.join(server.MAPS_DIR, "russia_meta.json"))


def test_russia_map_hidden_in_ui_and_listings(client, auth_headers):
    home_res = client.get("/")
    assert home_res.status_code == 200
    html = home_res.text
    assert "rostov_quiz_map.html" in html
    assert "krasnodar_quiz_map.html" in html
    assert "russia_quiz_map.html" not in html
    assert '<option value="russia">' not in html
    assert '"russia_map_enabled": false' in html

    admin_res = client.get("/admin", headers=auth_headers)
    assert admin_res.status_code == 200
    assert "rostov_quiz_map.html" in admin_res.text
    assert "russia_quiz_map.html" not in admin_res.text
    assert '"russia_map_enabled": false' in admin_res.text

    maps_res = client.get("/api/maps")
    assert maps_res.status_code == 200
    filenames = {m["filename"] for m in maps_res.json()}
    assert "rostov_quiz_map.html" in filenames
    assert "russia_quiz_map.html" not in filenames

    dash_res = client.get("/api/student/dashboard?email=student@sfedu.ru")
    assert dash_res.status_code == 200
    regions = dash_res.json()["regions"]
    assert "rostov" in regions
    assert "krasnodar" in regions
    assert "russia" not in regions


def test_russia_map_direct_urls_render_friendly_notice(client):
    direct_urls = [
        "/russia_quiz_map.html",
        "/russia",
        "/rf",
        "/map/russia",
        "/map/rf",
        "/map?region=russia",
        "/region/russia",
        "/?region=russia",
        "/public/maps/russia_quiz_map.html",
    ]
    for url in direct_urls:
        res = client.get(url)
        assert res.status_code == 503, f"Expected 503 for {url}, got {res.status_code}"
        assert "Карта России временно находится в разработке. Скоро она станет доступна" in res.text
        assert 'href="/"' in res.text
        assert 'href="/map/rostov"' in res.text
        assert "GeoJSON" not in res.text


def test_russia_specific_apis_are_blocked_when_disabled(client, auth_headers):
    for api_url in (
        "/api/region/russia/data",
        "/api/region/rf/data",
        "/api/region/context?region=russia",
        "/api/region/russia/context",
        "/public/maps/russia_meta.json",
        "/russia_meta.json",
    ):
        res = client.get(api_url)
        assert res.status_code == 503, f"Expected 503 for {api_url}, got {res.status_code}"
        assert "временно находится в разработке" in res.text

    duel_res = client.post(
        "/api/duel/create",
        json={"mode": "center", "region": "russia", "host_name": "Тест"},
    )
    assert duel_res.status_code == 503

    exam_res = client.post(
        "/api/exam/launch",
        headers=auth_headers,
        json={
            "groupId": "g1",
            "groupName": "G1",
            "mapUrl": "russia_quiz_map.html",
            "regionName": "Российская Федерация",
            "quizType": "center",
            "quizTypeName": "Административные центры",
        },
    )
    assert exam_res.status_code == 503


def test_other_regional_maps_continue_working(client):
    for url in ("/rostov_quiz_map.html", "/map/rostov", "/map/krasnodar", "/map/adygey", "/?region=rostov"):
        res = client.get(url)
        assert res.status_code == 200, f"Expected 200 for {url}, got {res.status_code}"
        assert "/quiz.js?v=" in res.text

    for api_url in ("/api/region/rostov/data", "/api/region/adygey/data", "/api/region/context?region=rostov"):
        res = client.get(api_url)
        assert res.status_code == 200, f"Expected 200 for {api_url}, got {res.status_code}"

    duel_res = client.post(
        "/api/duel/create",
        json={"mode": "center", "region": "rostov", "host_name": "Ростов Игрок"},
    )
    assert duel_res.status_code == 200
    assert duel_res.json()["region"] == "rostov"


def test_russia_map_reenables_with_single_flag(client, monkeypatch):
    monkeypatch.setattr(server, "RUSSIA_MAP_ENABLED", True)

    home_res = client.get("/")
    assert home_res.status_code == 200
    assert "russia_quiz_map.html" in home_res.text
    assert '"russia_map_enabled": true' in home_res.text

    map_res = client.get("/map/russia")
    assert map_res.status_code == 200

    api_res = client.get("/api/region/russia/data")
    assert api_res.status_code == 200

    dash_res = client.get("/api/student/dashboard?email=student@sfedu.ru")
    assert dash_res.status_code == 200
    assert "russia" in dash_res.json()["regions"]
