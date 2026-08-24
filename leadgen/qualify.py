"""Tariff-refund qualification/scoring for importer candidates.

Stage 50: prioritize prospects from importer evidence. Scoring is transparent,
deterministic, and retains reasons so sales can see why a lead ranked highly.
"""
from __future__ import annotations

from datetime import date, datetime


def _num(value, default=0.0):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default


def _date(value):
    if not value:
        return None
    text = str(value)[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def score(row: dict, today: date | None = None) -> dict:
    today = today or date.today()
    points = 0
    reasons = []

    shipments = _num(row.get("shipments"))
    if shipments >= 1000:
        points += 30; reasons.append("1000+ shipments")
    elif shipments >= 250:
        points += 25; reasons.append("250+ shipments")
    elif shipments >= 50:
        points += 18; reasons.append("50+ shipments")
    elif shipments >= 10:
        points += 10; reasons.append("10+ shipments")
    elif shipments > 0:
        points += 4; reasons.append("active shipment history")

    last = _date(row.get("last_shipment"))
    if last:
        age = (today - last).days
        if age <= 90:
            points += 25; reasons.append("shipment within 90 days")
        elif age <= 180:
            points += 20; reasons.append("shipment within 180 days")
        elif age <= 365:
            points += 12; reasons.append("shipment within 12 months")
        elif age <= 730:
            points += 5; reasons.append("shipment within 24 months")

    countries = row.get("origin_countries") or row.get("countries") or []
    if isinstance(countries, str):
        countries = [countries]
    country_text = " ".join(map(str, countries)).lower()
    if "china" in country_text or "cn" in [str(x).lower() for x in countries]:
        points += 25; reasons.append("China import exposure")

    tariff = row.get("tariff_exposure")
    if tariff is True or str(tariff).lower() in {"yes", "high", "confirmed"}:
        points += 20; reasons.append("tariff exposure confirmed")

    # Cap at 100 for a stable sales-priority scale.
    points = min(points, 100)
    if points >= 70:
        tier = "A"
    elif points >= 50:
        tier = "B"
    elif points >= 30:
        tier = "C"
    else:
        tier = "RESEARCH"

    out = dict(row)
    out["qualification_score"] = points
    out["qualification_tier"] = tier
    out["qualification_status"] = "QUALIFIED" if points >= 50 else "RESEARCH"
    out["qualification_reason"] = "; ".join(reasons) or "insufficient importer evidence"
    return out


def qualify(rows: list[dict]) -> list[dict]:
    ranked = [score(r) for r in rows]
    return sorted(ranked, key=lambda r: (-r["qualification_score"], str(r.get("company_name") or "")))
