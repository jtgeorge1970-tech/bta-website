"""Build a deterministic enrichment queue from qualified prospects."""
from __future__ import annotations
import csv, json
from pathlib import Path
from apollo_enrichment import search_request

OUTPUT=Path("leadgen/output")
QUALIFIED=OUTPUT/"qualified_importers.csv"
QUEUE=OUTPUT/"enrichment_queue.json"


def load_qualified(path: Path=QUALIFIED) -> list[dict]:
    if not path.exists(): return []
    with path.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))


def build(rows: list[dict]) -> list[dict]:
    queue=[]
    for row in rows:
        if str(row.get("qualification_status"))!="QUALIFIED": continue
        if row.get("contact_name") and row.get("phone") and row.get("email"): continue
        queue.append({
            "company_id":row.get("company_id"), "company_name":row.get("company_name"),
            "domain":row.get("domain") or row.get("website"),
            "qualification_score":row.get("qualification_score"),
            "qualification_tier":row.get("qualification_tier"),
            "apollo_search":search_request(row), "enrichment_status":"PENDING_SEARCH"
        })
    queue.sort(key=lambda x: (-float(x.get("qualification_score") or 0),str(x.get("company_name") or "")))
    return queue


def run():
    queue=build(load_qualified()); QUEUE.parent.mkdir(parents=True,exist_ok=True)
    QUEUE.write_text(json.dumps(queue,indent=2),encoding="utf-8")
    return {"queued":len(queue)}

if __name__=="__main__": print(json.dumps(run(),indent=2))
