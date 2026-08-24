"""Deduplication for BTA importer lead machine."""
import re


def norm(value):
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def identity_keys(row):
    keys = set()
    for field in ("company_id", "company_name", "website", "domain", "email", "phone"):
        value = norm(row.get(field))
        if value:
            keys.add((field, value))
    return keys


def split_new(candidates, existing):
    """Return (new, duplicates). Company ID/name/domain are primary identity checks."""
    existing_keys = set()
    for row in existing:
        existing_keys |= identity_keys(row)
    new, duplicates = [], []
    for row in candidates:
        overlap = identity_keys(row) & existing_keys
        if overlap:
            duplicates.append({"record": row, "matched_on": sorted(overlap)})
        else:
            new.append(row)
            existing_keys |= identity_keys(row)
    return new, duplicates
