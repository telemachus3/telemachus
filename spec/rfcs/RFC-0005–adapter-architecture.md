---
RFC: 0005
Title: Adapter Architecture & Provider Modules
Version: 0.1-draft
Status: Draft
Author: Sébastien Edet
Date: 2025-10-13
Project: Telemachus Specification
---

## 1. Purpose

This RFC defines the architecture, naming conventions, and implementation guidelines for **Telemachus Adapters**, which are responsible for transforming external telematics data (from APIs, SDKs, or proprietary feeds) into valid Telemachus Records.

Adapters act as bridges between real-world data sources — such as Webfleet, Samsara, Geotab, or RS3 simulations — and the standardized Telemachus Dataset format described in RFC-0003.

---

## 2. Scope

The specification covers:
- Python module structure for adapters (`telemachus.adapters.*`)
- Interface and base classes for data ingestion
- Mapping conventions between provider fields and Telemachus FieldGroups
- Validation and testing procedures
- Integration with CLI and dataset generation tools

---

## 3. Relationship to Other RFCs

| RFC | Title | Dependency |
|------|--------|-------------|
| RFC-0001 | Telemachus Core 0.2 | Defines the base record structure |
| RFC-0002 | Comparative Telematics API Formats | Provides reference field mappings |
| RFC-0003 | Dataset Specification 0.2 | Defines dataset-level metadata |
| RFC-0004 | Extended FieldGroups Schema | Defines extended telemetry fields |
| RFC-0007 | Validation Framework & CLI Rules | Ensures consistency in output |

---

## 4. Architecture Overview

Each adapter module converts provider-specific data into a canonical Telemachus structure.

```
Provider API → Adapter (Parser + Mapper) → Telemachus Record → Dataset
```

Adapters may implement one or several components:
- **Fetcher** — retrieves data via REST, MQTT, CSV, or SDK  
- **Parser** — interprets raw payloads (JSON, XML, binary)  
- **Mapper** — maps provider fields to Telemachus schema  
- **Normalizer** — applies unit conversions and alignment  
- **Validator** — ensures structural compliance  

---

## 5. Module Layout

All adapters must reside under the `telemachus.adapters` namespace.

```
telemachus/
 └── adapters/
      ├── base.py
      ├── webfleet/
      │    ├── __init__.py
      │    └── mapper.py
      ├── samsara/
      │    ├── __init__.py
      │    └── mapper.py
      ├── geotab/
      │    └── mapper.py
      ├── teltonika/
      │    └── parser.py
      └── rs3/
           └── mapper.py
```

---

## 6. Base Interface

Each adapter must implement a subclass of `BaseAdapter`, defined as:

```python
class BaseAdapter:
    provider: str
    version: str

    def fetch(self, **kwargs) -> Any:
        """Optional: Retrieve raw provider data."""
        raise NotImplementedError

    def parse(self, raw: Any) -> list[dict]:
        """Convert raw provider data to intermediate dicts."""
        raise NotImplementedError

    def map_record(self, record: dict) -> dict:
        """Map provider fields to Telemachus FieldGroups."""
        raise NotImplementedError

    def normalize(self, record: dict) -> dict:
        """Apply type conversions, units, and alignment."""
        raise NotImplementedError

    def to_telemachus(self, record: dict) -> dict:
        """Return a fully valid Telemachus Record."""
        r = self.map_record(record)
        return self.normalize(r)
```

---

## 7. Field Mapping Conventions

Mappings between provider and Telemachus fields must:
- Be stored as YAML files under `mappings/<provider>.yaml`
- Follow the convention: `provider_field: telemachus_field`
- Support alias resolution for provider field variants

Example (`mappings/webfleet.yaml`):

```yaml
gps.latitude: position.lat
gps.longitude: position.lon
vehicle.speed: speed.kmh
engine.rpm: engine.rpm
fuel.level: fuel.level_pct
```

These mappings are version-controlled and validated by automated tests.

---

## 8. Adapter Metadata

Each adapter includes a metadata descriptor (`adapter.json`):

```json
{
  "provider": "samsara",
  "version": "2025-10",
  "author": "Telemachus Project",
  "fields_supported": ["position", "speed", "engine", "fuel"],
  "source_type": "API",
  "license": "MIT"
}
```

This ensures discoverability and consistent documentation across all adapters.

---

## 9. Integration with CLI

Adapters integrate into the Telemachus CLI as follows:

```bash
telemachus adapter list
telemachus adapter fetch samsara --vehicle-id=123
telemachus adapter convert webfleet input.json output.csv
```

Each adapter exposes entry points via the `telemachus.adapters` namespace, automatically discovered by the CLI.

---

## 10. Testing and Validation

Each adapter must include:
- Unit tests validating its mapping correctness
- End-to-end tests producing a sample Telemachus dataset
- Schema compliance tests (via `telemachus validate`)
- Optional mock data under `tests/data/<provider>/`

A CI workflow ensures all adapters remain consistent with the latest Telemachus schema.

---

## 11. Example Workflow

Example using the Samsara adapter:

```python
from telemachus.adapters.samsara import SamsaraAdapter

adapter = SamsaraAdapter()
raw = adapter.fetch(api_key="XXX")
records = adapter.parse(raw)
tele_records = [adapter.to_telemachus(r) for r in records]
```

Generates a validated dataset ready for:
```bash
telemachus dataset create --from samsara --out datasets/2025-10-13-v0.2
```

---

## 12. Extension Strategy

Future adapters will support:
- File-based formats (CSV, Parquet, Excel)
- MQTT / Kafka live ingestion
- Hybrid data sources (e.g., Teltonika codecs)
- Bidirectional conversion (Telemachus → provider)

New adapters must follow naming:  
`telemachus.adapters.<provider>` and include RFC reference in README.

---

## 13. References

- RFC-0001 — *Telemachus Core 0.2*  
- RFC-0002 — *Comparative Telematics API Formats*  
- RFC-0003 — *Dataset Specification 0.2*  
- RFC-0004 — *Extended FieldGroups Schema*  
- RFC-0007 — *Validation Framework & CLI Rules*  
- Webfleet Connect API — https://www.webfleet.com/static/help/webfleet-connect/en_gb/index.html  
- Samsara API — https://developers.samsara.com/reference/overview  
- Geotab API — https://developers.geotab.com/myGeotab/introduction/  
- Teltonika Codec — https://wiki.teltonika-gps.com/view/Codec  

---

## 14. Conclusion

This RFC formalizes the design of the Telemachus Adapter Layer.  
It provides a unified interface to ingest, normalize, and validate external fleet and simulated data, ensuring interoperability between heterogeneous data providers and the Telemachus open standard.