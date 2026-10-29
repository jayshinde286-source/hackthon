# Scientific Limitations & Engineering Caveats

This document explicitly defines the boundaries and fundamental limitations of non-restorative integrity verification.

---

## 1. Why Compressed File Size Cannot Prove Completeness
A compressed export file that becomes smaller despite containing more records is **not** evidence of corruption:
- Compression algorithms (such as DEFLATE in Gzip, Bzip2 Burrows-Wheeler, or LZMA) rely on finding repetitive byte patterns and replacing them with short backward distance/length references.
- If a newer export has more rows with repeated categorical values (e.g., status codes, customer tiers, timestamps, or NULL-like entries), the dictionary compression ratio increases dramatically.
- In our empirical benchmarks:
  - 100,000 diverse records compressed to **3.09 MB** (ratio: 4.60x).
  - 130,000 repetitive records compressed to **385 KB** (ratio: 46.61x).
  - The file size dropped by **87.5%** despite having **30% more rows**, yet every row was structurally intact and uncorrupted.

---

## 2. Why a Valid Decompression Test Does Not Prove Source Completeness
- A successful decompression test confirms only that:
  1. The compression container framing is structurally intact.
  2. The byte stream is decodable by the standard decompression library.
  3. The container's embedded CRC-32 checksum and uncompressed ISIZE trailer match the decompressed byte stream.
- **What it does NOT prove:**
  - It cannot prove that the database export process (`mysqldump`, `pg_dump`, or custom script) included every row from the source table.
  - If an export process prematurely terminated or executed `SELECT * FROM tbl WHERE status='ACTIVE'` instead of dumping the whole table, the resulting gzip file can be 100% valid while omitting 50% of the database data!

---

## 3. Why Post-Hoc Hashes Cannot Prove Historical Source Completeness
- Computing a SHA-256 hash from a suspicious export file after it has already been generated establishes an immutable **identity reference** for that file going forward.
- However, if the export dropped 10,000 rows during generation, hashing that damaged file simply establishes a hash of the incomplete dataset.
- Conclusive proof of source completeness requires an **independent trusted manifest** generated synchronously at export creation time by the export pipeline or verified directly against database source audit metrics.

---

## 4. Why SQL Dialect Support Must Be Explicitly Scoped
- SQL dumps vary drastically across database engines (MySQL backtick escapes, PostgreSQL dollar-quoted strings, Oracle pl/sql blocks, procedural routines).
- Claiming universal SQL dump parsing without executing SQL or embedding a full relational database parser is technically unsupportable.
- DBGuard explicitly scopes SQL support to standard MySQL `INSERT INTO table VALUES (...), (...)` and PostgreSQL `COPY table FROM stdin;` formats using a deterministic lexical state machine.

---

## 5. Anomaly Detection is Not Corruption Detection
- An anomaly flag (such as `RULE_SIZE_DROP_ROW_INCREASE`) is an alert signaling unexpected variance that warrants investigation.
- It is not a definitive declaration of corruption. Conflating statistical anomalies with verification failures leads to false alarms and erroneous operational decisions.

