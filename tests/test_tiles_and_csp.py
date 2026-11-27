def test_security_csp_allows_basemap_and_cdn(client):
    res = client.get("/")
    assert res.status_code == 200
    csp = res.headers.get("Content-Security-Policy", "")
    assert "https://basemaps.cartocdn.com" in csp
    assert "https://*.basemaps.cartocdn.com" in csp
    assert "https://*.arcgisonline.com" in csp
    assert "https://*.openstreetmap.org" in csp
    assert "https://cdn.jsdelivr.net" in csp


def test_carto_tile_proxy_validation(client):
    res_bad_style = client.get("/tiles/carto/invalid/7/78/44.png")
    assert res_bad_style.status_code == 400

    res_bad_zoom = client.get("/tiles/carto/voyager/25/0/0.png")
    assert res_bad_zoom.status_code == 400

    res_bad_coord = client.get("/tiles/carto/voyager/2/99/0.png")
    assert res_bad_coord.status_code == 400


def test_carto_tile_proxy_missing_key_triggers_fallback_error(client, monkeypatch):
    import server
    monkeypatch.setenv("CARTO_KEY", "")
    server._TILE_CACHE.clear()
    res = client.get("/tiles/carto/voyager/7/78/44.png")
    assert res.status_code == 503


def test_map_response_hides_carto_key_and_busts_css_cache(client):
    res = client.get("/rostov_quiz_map.html")
    assert res.status_code == 200
    html = res.text
    assert "/tiles/carto/voyager/{z}/{x}/{y}.png" in html
    assert "?key=" not in html
    assert '"collapsed": false' in html
    assert "/public/map.css?v=" in html
    assert "/quiz.js?v=" in html
    assert "var DuelManager =" not in html
    assert "no-cache" in res.headers.get("Cache-Control", "")
