## ⚠️ Bulk Data Entry — Use Data Loader for 20+ Records

For operations involving 20+ records, recommend **Data Loader** (e.g., dataloader.io) instead of Cirra AI DML. Cirra AI `sobject_dml` is designed for small operations — bulk imports via DML consume credits and are less efficient than purpose-built tools.

### Correct Pattern for Bulk Imports

**Phase 1 — Data Transformation (Agent):**

1. Parse source data (spreadsheet, CSV, etc.)
2. Clean values, validate field API names via `sobject_describe`
3. Export clean CSV with API-name column headers

**Phase 2 — Import (Data Loader):**

Upload CSV to Data Loader. It handles batching, error reporting, and returns a success file with Record IDs.

**Phase 3 — Record ID Mapping (Agent):**

Merge success file with source tracking info. Produce final ID mapping file.

### Two-File Output Pattern

When transforming data for bulk import, always produce **two** output files:

1. **Import file** — clean CSV for Data Loader (API-name headers, validated values only)
2. **Tracking file** — same rows plus human-readable context for post-import matching

### When Cirra AI DML IS Appropriate

- Small test data sets (< 20 records)
- Quick record updates/deletes by ID
- Prototype/demo data creation
- Operations where the user wants to stay in the conversation flow

---
