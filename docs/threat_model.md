# DBGuard Threat Model & Security Architecture

## 1. Trust Assumptions & Attack Surface
DBGuard is designed to operate in environments where uploaded database exports, filenames, and manifest files originate from potentially untrusted or compromised sources.

### Threat Actors Considered:
- **Malicious Insiders:** Users submitting weaponized zip bombs or crafted payloads designed to exhaust server RAM or disk tablespace.
- **Data Tampering Attackers:** Adversaries who modify table rows or delete records in an export archive while attempting to evade row count detection.
- **Untrusted Manifest Producers:** Entities providing forged manifest files claiming false record counts.

---

## 2. Threat Analysis & Mitigations

| Threat Category | Potential Attack Vector | Severity | DBGuard Mitigation |
|---|---|---|---|
| **Resource Exhaustion** | Decompression Bomb (e.g. tiny archive expanding to gigabytes) | High | Enforces strict maximum decompressed byte limit (`max_decompressed_size_bytes`) and expansion ratio ceiling (`max_expansion_ratio`, default 100x). Decompression aborts immediately upon violation. |
| **Path Traversal** | Filenames with `../` or null bytes (`\0`) | High | `validate_input_path` and `safe_output_path` sanitize paths, reject null bytes, resolve canonical paths, and prevent writing outside intended output folders. |
| **SQL Injection & RCE** | Embedded SQL payloads (`DROP TABLE`, `EXEC()`) in SQL dump files | Critical | **Zero-Execution Invariant:** DBGuard never executes SQL statements, never opens a database socket, and uses a tokenizer/state machine to count rows without executing DML/DDL. |
| **Data Privacy Leakage** | Sensitive customer data leaking into server logs or debug traces | High | Sanitized logging: log handlers never print cell values. Reports contain only column names, inferred data types, line numbers, and aggregate counts. |
| **File Clobbering** | Overwriting original export archives during analysis | High | Non-destructive invariant: all operations open inputs in read-only binary mode (`"rb"`). Automated tests confirm file bytes and timestamps remain unmodified. |
| **Manifest Forgery** | Tampering with manifest JSON to declare matching hashes | High | Cryptographic HMAC-SHA256 signature verification over canonicalized manifest JSON with key management support. |

---

## 3. Residual Risks & Operational Caveats
- **Offline Attacks on HMAC Keys:** If the HMAC secret key is compromised on the database server, an adversary can sign altered manifests.
- **Hardware Bit-Flips:** Memory corruption during computation is not defended against without ECC RAM on the host system.

