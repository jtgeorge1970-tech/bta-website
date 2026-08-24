# BTA Tariff Refund Lead Machine

## Stage status: 40%

The discovery/queue stage is implemented.

### What is now automated

1. Query ImportYeti's U.S.-import company dataset using `IMPORTYETI_API_KEY`.
2. Normalize importer candidates.
3. Deduplicate candidates against the existing lead universe.
4. Preserve duplicate audit records.
5. Split leads into two operational queues:
   - `call_ready.csv`: **contact name + verified phone + verified email required**.
   - `contact_required.csv`: attractive candidates that still need verified contact data.
6. Never promote guessed contact information to the call-ready queue.

### Files

- `importyeti_client.py` — ImportYeti API client and candidate normalization.
- `dedupe.py` — cross-run importer deduplication.
- `pipeline.py` — discovery, dedupe, and two-queue orchestration.
- `validate_contacts.py` — strict phone/email validation and source requirements.

### Run

Set the ImportYeti API key in the runtime environment (never commit it):

```bash
export IMPORTYETI_API_KEY='...'
python leadgen/pipeline.py --filters-json '{}'
```

Production PowerQuery filters should target the tariff-refund profile: active U.S. importers, especially meaningful China exposure and higher shipment volume. Qualification and contact-enrichment adapters are the next stage; until they verify contact data, records remain `CONTACT_REQUIRED`.

### Output contract

The machine deliberately maintains two lists because a company is not ready to call merely because it is a good tariff-refund prospect. `CALL_READY` requires a real contact name plus phone and email, with source references for both contact methods.
