# DBGuard Integrity Manifests

Integrity manifests store independent, cryptographic assertions generated either synchronously at export creation time or post-hoc for observational identity.

## Schema Version 1.0 Specification
Each manifest JSON complies with `dbguard.manifest.schema.CURRENT_MANIFEST_VERSION`:

- `manifest_version`: Version string (`"1.0"`).
- `export_id`: Unique export identifier.
- `export_timestamp_utc`: ISO 8601 UTC timestamp.
- `source_identifier`: Database table or source identifier.
- `export_format`: Format (`csv`, `jsonl`, `sql_dump`).
- `compression_format`: Format (`gzip`, `bz2`, `xz`, `zstandard`).
- `schema_fingerprint`: SHA-256 digest over canonical column names and inferred types.
- `expected_row_count`: Exact data record count excluding header.
- `uncompressed_size_bytes`: Total byte count of decompressed stream.
- `uncompressed_sha256`: Cryptographic SHA-256 over exact uncompressed byte stream.
- `chunking_scheme`: Chunking method (`"fixed_bytes_1MB"`).
- `chunk_hashes`: Array of chunk descriptors with byte boundaries and individual SHA-256 digests.
- `trusted_reference_status`: Provenance indicator:
  - `TRUSTED_EXPORT_PIPELINE`: Generated synchronously by export utility.
  - `INDEPENDENT_SOURCE`: Provided by independent audit system.
  - `OBSERVATIONAL_POST_HOC`: Generated after-the-fact from the file itself (cannot prove source completeness).
  - `UNKNOWN`: Unverified provenance.
- `signature`: Optional HMAC-SHA256 signature sealing the manifest against tampering.

