# BTA Tariff Refund Lead Machine

## Stage status: 50% — qualification/scoring complete

The machine now handles discovery → normalization → dedupe → tariff qualification/scoring → queue routing.

### Automated stages

1. Query ImportYeti U.S.-import company data.
2. Normalize importer candidates while retaining raw evidence.
3. Deduplicate against the existing lead universe.
4. Score prospects from 0–100 using shipment scale, recency, China exposure and confirmed tariff exposure.
5. Rank prospects into A / B / C / RESEARCH tiers. A/B (50+) are qualified for contact work.
6. Route qualified leads with complete sourced contact data to `call_ready.csv`.
7. Route qualified leads with contact gaps to `contact_required.csv`.
8. Route lower-scoring importers to `research.csv` rather than polluting the call list.
9. Preserve `qualified_importers.csv` and duplicate audit records.

### Files

- `importyeti_client.py` — ImportYeti API client and normalization.
- `dedupe.py` — cross-run identity deduplication.
- `qualify.py` — deterministic tariff prospect scoring/ranking.
- `validate_contacts.py` — strict contact/source validation.
- `pipeline.py` — production orchestration and queue routing.
- `test_qualify.py` — dependency-free scoring/validation regression tests.

### Output contract

`CALL_READY` means the company is qualified AND has a real contact name, valid phone, valid email, and source references. Populated-but-unsourced contact data is never treated as validated.

### Next stage: 50% → 60%

Contact enrichment: resolve the best decision-maker and validated phone/email for `CONTACT_REQUIRED` records. Apollo can be used as an enrichment adapter, but credit-consuming enrichment is never executed without the required user approval.
