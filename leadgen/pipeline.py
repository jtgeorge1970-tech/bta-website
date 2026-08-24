"""BTA Tariff Refund Lead Machine — discovery, scoring, dedupe, routing."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
from typing import Iterable
from dedupe import split_new
from importyeti_client import search_importers, normalize_company
from qualify import qualify
from validate_contacts import audit

OUTPUT=Path("leadgen/output")
EXISTING=OUTPUT/"existing_leads.json"; CANDIDATES=OUTPUT/"importer_candidates.json"
QUALIFIED=OUTPUT/"qualified_importers.csv"; CALL_READY=OUTPUT/"call_ready.csv"
CONTACT_REQUIRED=OUTPUT/"contact_required.csv"; RESEARCH=OUTPUT/"research.csv"; DUPLICATES=OUTPUT/"duplicates.json"
FIELDS=["company_id","company_name","address","shipments","last_shipment","origin_countries","website","domain","contact_name","contact_title","phone","email","phone_source","email_source","contact_source","qualification_score","qualification_tier","qualification_status","qualification_reason","lead_status"]

def _rows(payload):
    raw=payload.get("data") or payload.get("results") or payload.get("companies") or []
    rows=[]
    for x in raw:
        r=normalize_company(x)
        # Preserve useful tariff evidence exposed by upstream records.
        r["origin_countries"]=x.get("origin_countries") or x.get("countries") or x.get("country") or []
        r["tariff_exposure"]=x.get("tariff_exposure") or x.get("tariffExposure")
        r["website"]=x.get("website") or x.get("domain")
        r["domain"]=x.get("domain")
        rows.append(r)
    return rows

def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

def save_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data,indent=2,default=str),encoding="utf-8")

def write_csv(path,rows:Iterable[dict]):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="ignore"); w.writeheader()
        for r in rows: w.writerow({k:r.get(k,"") for k in FIELDS})

def route(rows):
    ready=[]; contact=[]; research=[]
    for row in rows:
        row=dict(row)
        if row["qualification_status"]!="QUALIFIED":
            row["lead_status"]="RESEARCH"; research.append(row); continue
        check=audit(row)
        if check["valid"]:
            row["lead_status"]="CALL_READY"; ready.append(row)
        else:
            row["lead_status"]="CONTACT_REQUIRED"; row["contact_gaps"]=";".join(check["problems"]); contact.append(row)
    return ready,contact,research

def run(filters=None):
    OUTPUT.mkdir(parents=True,exist_ok=True)
    payload=search_importers(**(filters or {})); discovered=_rows(payload); save_json(CANDIDATES,discovered)
    new_rows,duplicates=split_new(discovered,load_json(EXISTING,[])); save_json(DUPLICATES,duplicates)
    ranked=qualify(new_rows); qualified=[r for r in ranked if r["qualification_status"]=="QUALIFIED"]
    ready,contact,research=route(ranked)
    write_csv(QUALIFIED,qualified); write_csv(CALL_READY,ready); write_csv(CONTACT_REQUIRED,contact); write_csv(RESEARCH,research)
    return {"discovered":len(discovered),"new":len(new_rows),"duplicates":len(duplicates),"qualified":len(qualified),"call_ready":len(ready),"contact_required":len(contact),"research":len(research)}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--filters-json",default="{}"); a=p.parse_args(); print(json.dumps(run(json.loads(a.filters_json)),indent=2))
if __name__=="__main__": main()
