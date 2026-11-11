def test_admin_groups_unauthorized(client):
    res = client.get("/api/admin/groups")
    assert res.status_code == 401

def test_admin_groups_ok(client, auth_headers):
    res = client.get("/api/admin/groups", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_admin_results_ok(client, auth_headers):
    res = client.get("/api/admin/results", headers=auth_headers)
    assert res.status_code == 200
