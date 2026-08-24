"""Strict contact validation for BTA tariff-refund leads.

No inferred or pattern-guessed email/phone is accepted. A usable value requires a
source URL/reference so the lead can be audited before calling.
"""
from __future__ import annotations

import re

EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_DIGITS = re.compile(r"\D+")


def valid_email(value: str | None) -> bool:
    return bool(value and EMAIL.match(value.strip()))


def valid_phone(value: str | None) -> bool:
    digits = PHONE_DIGITS.sub("", value or "")
    return 10 <= len(digits) <= 15


def audit(row: dict) -> dict:
    problems = []
    if not str(row.get("contact_name") or "").strip():
        problems.append("missing_contact_name")
    if not valid_phone(row.get("phone")):
        problems.append("missing_or_invalid_phone")
    if row.get("phone") and not str(row.get("phone_source") or "").strip():
        problems.append("unverified_phone")
    if not valid_email(row.get("email")):
        problems.append("missing_or_invalid_email")
    if row.get("email") and not str(row.get("email_source") or "").strip():
        problems.append("unverified_email")
    return {"valid": not problems, "problems": problems}
