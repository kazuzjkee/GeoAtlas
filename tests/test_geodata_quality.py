import copy
import json
import urllib.error
from pathlib import Path

import pytest

import geodata_monitor


def test_real_registry_passes_offline():
    report = geodata_monitor.build_quality_report(check_remote=False)
    assert report["summary"]["total_datasets"] == len(geodata_monitor.DATA_REGISTRY)
    assert report["summary"]["failed"] == 0
    assert report["summary"]["overall_status"] == "pass"

    by_id = {d["id"]: d for d in report["datasets"]}
    assert by_id["rostov_passports"]["territory_count"] == 55
    assert by_id["rostov_passports"]["coverage_pct"] == 100.0
    assert by_id["krasnodar_passports"]["territory_count"] == 44
    assert by_id["krasnodar_passports"]["coverage_pct"] == 100.0
    # Latest stat year preserved per indicator (not conflated with download date)
    rostov_inds = {i["key"]: i for i in by_id["rostov_passports"]["indicators"]}
    assert rostov_inds["births"]["latest_year"] == 2023
    assert rostov_inds["housing_commissioned"]["latest_year"] == 2025


def test_missing_metadata_and_missing_file_fail(tmp_path):
    bad_entry = copy.deepcopy(geodata_monitor.DATA_REGISTRY[0])
    bad_entry["local_path"] = "nonexistent/missing.json"
    bad_entry["license"] = ""
    res = geodata_monitor.evaluate_dataset(bad_entry, base_dir=tmp_path, check_remote=False)
    assert res["check_result"] == "fail"
    assert any("Отсутствует файл" in e for e in res["errors"])
    assert any("обязательные поля реестра" in e for e in res["errors"])


def test_duplicates_nulls_and_version_mismatch(tmp_path):
    # Create synthetic passport JSON with a duplicate OKTMO, a null value, and a version mismatch
    p = tmp_path / "sample_passports.json"
    payload = {
        "metadata": {
            "dataset_version": "v20260101",
            "updated_at": "2026-01-01",
            "license": "CC BY 4.0",
            "attribution": "Test attribution",
            "indicators": {
                "population_avg": {
                    "code": "41.8112013",
                    "name": "Население",
                    "unit": "Человек",
                    "latest_year": 2024,
                },
            },
        },
        "territories": {
            "60601000": {
                "oktmo": "60601000",
                "name": "Район 1",
                "indicators": {
                    "population_avg": {"latest_year": 2024, "latest_value": 1000, "series": {"2024": 1000}},
                },
            },
            "60601000_dup": {
                "oktmo": "60601000",
                "name": "Дубль",
                "indicators": {
                    "population_avg": {"latest_year": 2024, "latest_value": None, "series": {"2024": None}},
                },
            },
        },
    }
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    entry = {
        "id": "test_ds",
        "name": "Test DS",
        "kind": "passport_json",
        "region": "Тест",
        "local_path": "sample_passports.json",
        "expected_territories": 2,
        "source": "Test",
        "source_url": "https://example.com",
        "owner_org": "Test",
        "license": "CC BY 4.0",
        "attribution": "Test",
        "declared_version": "v20260928",
        "remote_check_type": "static_local",
    }
    res = geodata_monitor.evaluate_dataset(entry, base_dir=tmp_path, check_remote=False)
    assert res["check_result"] == "fail"
    assert res["missing_total"] == 1
    assert res["coverage_pct"] == 50.0
    assert any("дублирующий ОКТМО" in e for e in res["errors"])
    assert any("Несовпадение версии" in w for w in res["warnings"])


def test_remote_freshness_unknown_vs_stale_and_fresh(monkeypatch):
    # 1. Network error -> unknown, NEVER stale
    def _fail_urlopen(*args, **kwargs):
        raise urllib.error.URLError("timeout")

    monkeypatch.setattr(geodata_monitor.urllib.request, "urlopen", _fail_urlopen)
    entry = copy.deepcopy(geodata_monitor.DATA_REGISTRY[0])
    res_unknown = geodata_monitor.evaluate_dataset(entry, check_remote=True)
    assert res_unknown["freshness_status"] == "unknown"
    assert res_unknown["newer_available"] is False
    assert res_unknown["check_result"] == "pass"

    # 2. Newer remote version -> stale
    res_stale = geodata_monitor.evaluate_dataset(
        entry,
        check_remote=True,
        remote_checker=lambda _v: {
            "freshness_status": "stale",
            "remote_version": "v20261201",
            "newer_available": True,
            "note": "Newer version available",
        },
    )
    assert res_stale["freshness_status"] == "stale"
    assert res_stale["newer_available"] is True
    assert res_stale["remote_version"] == "v20261201"


def test_admin_quality_endpoints_and_public_sources_safety(anon_client, client, auth_headers):
    # Guest blocked from technical admin report
    assert anon_client.get("/api/admin/data-quality").status_code == 401

    # Student blocked with 403
    anon_client.post("/api/auth/register", json={
        "email": "dq_student@gmail.com",
        "password": "Password123",
        "password_confirm": "Password123",
        "full_name": "DQ Student",
        "accept_terms": True,
    })
    import auth_service, re
    code = next(m["code"] for m in reversed(auth_service.MOCK_MAILBOX) if m["to"] == "dq_student@gmail.com")
    anon_client.post("/api/auth/verify-code", json={"email": "dq_student@gmail.com", "code": code})
    assert anon_client.get("/api/admin/data-quality").status_code == 403

    # Admin gets full JSON report
    ok = client.get("/api/admin/data-quality", headers=auth_headers)
    assert ok.status_code == 200
    body = ok.json()
    assert body["summary"]["total_datasets"] == len(geodata_monitor.DATA_REGISTRY)

    # Public sources endpoint exposes no internal paths or sha256 hashes
    pub = anon_client.get("/api/data-sources")
    assert pub.status_code == 200
    pub_json = pub.text
    assert "Py_Geo" not in pub_json
    assert "sha256" not in pub_json
    assert len(pub.json()["sources"]) >= 2
