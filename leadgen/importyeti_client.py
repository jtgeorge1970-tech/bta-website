"""BTA Tariff Refund Lead Machine — ImportYeti discovery layer.

Stage 1: discover NEW U.S. importer candidates from ImportYeti PowerQuery.
Requires IMPORTYETI_API_KEY in the environment. No key is committed to GitHub.
"""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://data.importyeti.com/v1.0"
API_KEY = os.environ.get("IMPORTYETI_API_KEY", "")


def _get(path: str, params: dict | None = None) -> dict:
    if not API_KEY:
        raise RuntimeError("Set IMPORTYETI_API_KEY before running the lead machine.")
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def search_importers(**filters) -> dict:
    """Search U.S. import companies aggregated from bills of lading."""
    return _get("/powerquery/us-import/companies", filters)


def company(company_id: str) -> dict:
    return _get(f"/company/{urllib.parse.quote(str(company_id))}")


def company_bols(company_id: str, **params) -> dict:
    return _get(f"/company/{urllib.parse.quote(str(company_id))}/bols", params)


def normalize_company(raw: dict) -> dict:
    """Keep machine-critical fields while retaining the raw record for auditability."""
    return {
        "company_id": raw.get("id") or raw.get("companyId") or raw.get("company_id"),
        "company_name": raw.get("name") or raw.get("companyName") or raw.get("company_name"),
        "address": raw.get("address"),
        "shipments": raw.get("shipments") or raw.get("shipmentCount") or raw.get("shipment_count"),
        "last_shipment": raw.get("lastShipment") or raw.get("last_shipment"),
        "raw": raw,
    }


def save_candidates(payload: dict, out_path: str = "leadgen/output/importer_candidates.json") -> int:
    rows = payload.get("data") or payload.get("results") or payload.get("companies") or []
    normalized = [normalize_company(x) for x in rows]
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(normalized, indent=2, default=str), encoding="utf-8")
    return len(normalized)


if __name__ == "__main__":
    # Intentionally conservative default. Production filters are supplied by the runner.
    result = search_importers()
    count = save_candidates(result)
    print(f"Saved {count} importer candidates")
