"""Apollo contact-enrichment adapter for qualified tariff-refund prospects.

This module prepares company/domain-based decision-maker searches and normalizes
returned Apollo people into the BTA lead schema. Actual Apollo enrichment/reveal
must be executed through an authorized runtime/account and may consume credits.
No guessed email or phone is ever emitted.
"""
from __future__ import annotations

TARGET_TITLES = [
    "owner", "founder", "president", "chief executive officer", "ceo",
    "chief financial officer", "cfo", "controller", "vp finance",
    "vice president finance", "director of finance", "treasurer",
    "head of finance", "chief operating officer", "coo",
]
TARGET_SENIORITIES = ["owner", "founder", "c_suite", "vp", "director"]


def search_request(lead: dict) -> dict:
    domain = str(lead.get("domain") or lead.get("website") or "").strip()
    company = str(lead.get("company_name") or "").strip()
    req = {
        "person_titles": TARGET_TITLES,
        "person_seniorities": TARGET_SENIORITIES,
        "include_similar_titles": True,
        "contact_email_status": ["verified"],
        "per_page": 10,
        "page": 1,
    }
    if domain:
        domain = domain.removeprefix("https://").removeprefix("http://").split("/")[0]
        req["q_organization_domains_list"] = [domain]
    elif company:
        req["q_keywords"] = company
    return req


def person_priority(person: dict) -> tuple:
    title = str(person.get("title") or "").lower()
    seniority = str(person.get("seniority") or "").lower()
    order = ["owner", "founder", "president", "chief executive", "ceo", "chief financial", "cfo", "controller", "vp", "vice president", "director"]
    rank = next((i for i, word in enumerate(order) if word in title), len(order))
    senior = 0 if seniority in {"owner", "founder", "c_suite"} else 1
    return (senior, rank, str(person.get("name") or ""))


def choose_decision_maker(people: list[dict]) -> dict | None:
    if not people:
        return None
    return sorted(people, key=person_priority)[0]


def enrichment_request(person: dict, reveal_phone: bool = True) -> dict:
    """Use Apollo id from search; never reconstruct identity from masked names."""
    pid = person.get("id")
    if not pid:
        raise ValueError("Apollo person id is required before enrichment")
    return {"id": pid, "reveal_personal_emails": False, "reveal_phone_number": reveal_phone}


def apply_enrichment(lead: dict, person: dict, phone: str | None = None) -> dict:
    out = dict(lead)
    first = str(person.get("first_name") or "").strip()
    last = str(person.get("last_name") or "").strip()
    name = str(person.get("name") or f"{first} {last}").strip()
    email = str(person.get("email") or "").strip()
    out.update({
        "contact_name": name,
        "contact_title": person.get("title") or "",
        "contact_source": "Apollo",
        "apollo_person_id": person.get("id") or "",
        "linkedin_url": person.get("linkedin_url") or "",
    })
    if email:
        out["email"] = email
        out["email_source"] = "Apollo"
    if phone:
        out["phone"] = phone
        out["phone_source"] = "Apollo"
    return out
