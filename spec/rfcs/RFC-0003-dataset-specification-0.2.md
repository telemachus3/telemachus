---
RFC: 0003
Title: Dataset Specification 0.2
Version: 0.1-draft
Status: Draft
Author: Sébastien Edet
Date: 2025-10-13
Project: Telemachus Specification
---

## 1. Purpose

This RFC defines the **Telemachus Dataset Specification v0.2**, establishing a standard structure for storing and describing mobility and telemetry datasets. It builds upon the Core schema defined in RFC-0001 and introduces consistent dataset-level metadata, manifest rules, and file formats compatible with Telemachus validation tools and RS3 simulation outputs.

---

## 2. Scope

The specification covers:
- Dataset directory structure and file organization  
- Dataset manifest (`dataset.json`) schema  
- Accepted data file formats (CSV, Parquet, Arrow)  
- Metadata and versioning requirements  
- Validation logic for datasets using `telemachus-py`

It does not define the schema for individual signals (covered in RFC-0001 and RFC-0004).

---

## 3. Dataset Structure

Each dataset is a self-contained directory containing:
```
<dataset_name>/
 ├── dataset.json         # Manifest describing the dataset
 ├── samples.csv          # Main data file (Telemachus Records)
 ├── assets/              # Optional static or contextual data
 ├── docs/                # Optional documentation
 └── checksum.md5         # Optional integrity check
```

**Naming convention:**  
`YYYY-MM-DD-vX.Y` (e.g., `2025-10-01-v1.0`)

---

## 4. Manifest Specification (`dataset.json`)

### 4.1 Required fields
| Field | Type | Description |
|--------|------|-------------|
| `version` | string | Telemachus spec version used (e.g., "0.2") |
| `schema` | string | Path or URL of the schema applied |
| `created_at` | string (ISO 8601) | Dataset creation timestamp |
| `records` | integer | Number of samples |
| `sampling_rate_hz` | float | Frequency of data collection |
| `sources` | array | List of data origins (e.g., RS3, Samsara) |
| `description` | string | Human-readable description of the dataset |
| `contact` | string | Dataset author or maintainer |

### 4.2 Optional fields
| Field | Type | Description |
|--------|------|-------------|
| `tags` | array | Keywords for classification |
| `license` | string | SPDX license identifier |
| `links` | object | Related URLs (docs, DOI, repositories) |
| `checksum` | string | Optional MD5 or SHA256 hash for verification |

---

## 5. Data File Format

### 5.1 CSV
- Comma-separated UTF-8 encoded text file
- Header row mandatory
- Timestamps in ISO 8601 UTC
- Decimal separator: `.`
- Example:
  ```
  time,position.lat,position.lon,speed.kmh,heading.deg
  2025-10-01T12:00:00.000Z,48.8566,2.3522,50.2,175.3
  ```

### 5.2 Parquet
- Recommended for large datasets
- Column names must match Telemachus field names
- Compression: `snappy` by default

### 5.3 Arrow
- Optional high-performance binary representation
- Schema included in file metadata

---

## 6. Metadata Validation

A dataset is considered **valid** if:
1. `dataset.json` conforms to its JSON schema (`schema/dataset.schema.json`)  
2. All required files exist (`dataset.json`, data file)  
3. `records` matches the number of rows in the data file  
4. Field names are consistent with Telemachus schema  
5. Timestamps are monotonic and within defined tolerances  

Validation is performed via:
```bash
telemachus validate --dataset <path> [--strict]
```

---

## 7. Dataset Metadata Schema (excerpt)

```json
{
  "version": "0.2",
  "schema": "https://telemachus3.github.io/telemachus-spec/schema/dataset.schema.json",
  "created_at": "2025-10-01T09:30:00Z",
  "records": 131186,
  "sampling_rate_hz": 10.0,
  "sources": ["RS3", "Telemachus Simulator"],
  "description": "Simulated mobility dataset generated from RS3 core2 pipeline.",
  "license": "CC-BY-4.0",
  "contact": "sebastien.edet@telemachus.org"
}
```

---

## 8. Integration with Validation Tools

The `telemachus-py` library must:
- Provide a `Dataset` class capable of reading and validating datasets  
- Support `.from_path()` constructor detecting file format automatically  
- Expose metadata through a unified `.meta` property  
- Provide CLI validation (`telemachus validate --dataset`) returning standardized exit codes

---

## 9. Future Extensions

Planned extensions (RFC-0004 and RFC-0007):
- Support for multi-segment datasets (`segments/` folder)
- Integration with the extended FieldGroups (`engine`, `fuel`, `energy`)
- Dataset lineage tracking (RFC-0030)
- Machine learning dataset splits (`train/`, `test/`, `val/`)

---

## 10. References

- RFC-0001 — *Telemachus Core 0.2*  
- RFC-0002 — *Comparative Telematics API Formats*  
- RFC-0004 — *Extended FieldGroups Schema*  
- RFC-0007 — *Validation Framework & CLI Rules*  
- RFC-0011 — *Versioning and Governance Policy*  
- https://github.com/telemachus3/telemachus-spec  
- https://github.com/telemachus3/telemachus-datasets  

---

## 11. Conclusion

This RFC establishes the structural foundation for how datasets are defined, stored, and validated in Telemachus.  
It bridges simulation outputs (RS3) and real-world telemetry data under a unified manifest-based model, ensuring long-term reproducibility, traceability, and compatibility across the ecosystem.