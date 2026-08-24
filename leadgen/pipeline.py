"""BTA Tariff Refund Lead Machine — discovery-to-queue pipeline.

Stage 40 deliverable: turn ImportYeti discovery into two durable queues:
1) CALL_READY: only leads with verified name + phone + email
2) CONTACT_REQUIRED: qualified leads still missing verified contact data

This module deliberately does not guess contact data. Enrichment adapters can add
verified fields later; records remain in CONTACT_REQUIRED until complete.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable

from dedupe import split_new
from importyeti_client import search_importers, normalize_company

OUTPUT = Path("leadgen/output")
EXISTING = OUTPUT / "existing_leads.json"
CANDIDATES = OUTPUT / "importer_candidates.json"
CALL_READY = OUTPUT / "call_ready.csv"
CONTACT_REQUIRED = OUTPUT / "contact_required.csv"
DUPLICATES = OUTPUT / "duplicates.json"

FIELDS = [
    "company_id", "company_name", "address", "shipments", "last_shipment",
    "website", "domain", "contact_name", "contact_title", "phone", "email",
    "phone_source", "email_source", "contact_source", "qualification_status",
    "qualification_reason", "lead_status",
]


def _rows(payload: dict) -> list[dict]:
    raw = payload.get("data") or payload.get("results") or payload.get("companies") or []
    return [normalize_company(x) for x in raw]


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def verified(value, source) -> bool:
    return bool(str(value or "").strip() and str(source or "").strip())


def is_call_ready(row: dict) -> bool:
    return (
        bool(str(row.get("contact_name") or "").strip())
        and verified(row.get("phone"), row.get("phone_source"))
        and verified(row.get("email"), row.get("email_source"))
    )


def classify(rows: Iterable[dict]) -> tuple[list[dict], list[dict]]:
    ready, needs_contact = [], []
    for row in rows:
        row = dict(row)
        if is_call_ready(row):
            row["lead_status"] = "CALL_READY"
            ready.append(row)
        else:
            row["lead_status"] = "CONTACT_REQUIRED"
            needs_contact.append(row)
    return ready, needs_contact


def write_csv(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDS})


def run(filters: dict | None = None) -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    payload = search_importers(**(filters or {}))
    discovered = _rows(payload)
    save_json(CANDIDATES, discovered)

    existing = load_json(EXISTING, [])
    new_rows, duplicates = split_new(discovered, existing)
    save_json(DUPLICATES, duplicates)

    # Qualification/enrichment can populate these fields before reclassification.
    ready, needs_contact = classify(new_rows)
    write_csv(CALL_READY, ready)
    write_csv(CONTACT_REQUIRED, needs_contact)

    return {
        "discovered": len(discovered),
        "new": len(new_rows),
        "duplicates": len(duplicates),
        "call_ready": len(ready),
        "contact_required": len(needs_contact),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--filters-json", default="{}", help="ImportYeti PowerQuery filters as JSON")
    args = parser.parse_args()
    summary = run(json.loads(args.filters_json))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
