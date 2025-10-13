# Telemachus Core Specification (v0.2)

Welcome to the **Telemachus Core** documentation for version 0.2.  
This documentation now represents Telemachus v0.2, aligned with the RFC-driven governance process (RFC-0011).  
This project defines an **open pivot format** for B2B telematics data (GNSS, IMU, CAN, Events, Context).  
It aims to unify fragmented data from providers (Geotab, Webfleet, Samsara, etc.) into a single, neutral schema.

The Core Specification is defined in RFC-0001 and forms the foundation for datasets, adapters, and validation tools.

## ❓ Why Telemachus?

- Open: A transparent and accessible format for all stakeholders.  
- Extensible: Designed to accommodate evolving telematics data types and sources.  
- Interoperable: Bridges diverse providers and systems under a unified schema.  
- Bridging science and business: Facilitates both research innovation and practical applications.

## 👥 Who is it for?

- Researchers: Access standardized data for analysis and modeling.  
- Developers/Integrators: Simplify integration with multiple telematics providers.  
- Fleet Operators/Insurers: Leverage consistent data for operations, monitoring, and risk assessment.

---

## 📚 Quick links
- 👉 [Introduction](01_introduction.md)
- 📖 [State of the Art](02_state_of_the_art.md)
- 📐 [Core Specification v0.2](03_spec_core.md)
- 📄 [RFCs Overview](../rfcs/)
- 🗺️ [Provider Mappings](05_provider_mappings.md)
- ⚙️ [Versioning & Governance](08_versioning.md)
- 🧪 [Examples](04_examples.md)
- 🧾 [JSON Schema](https://raw.githubusercontent.com/telemachus3/telemachus-spec/main/schemas/telemachus_core_v0.2.json)

---

## 🚀 Quickstart

Validate provided examples against the schema:

```bash
# Install ajv-cli and ajv-formats
npm install -g ajv-cli ajv-formats

# Validate all example files
ajv validate -c ajv-formats -s schemas/telemachus.schema.json -d "examples/*.json"
```

---

## 🌍 Vision

Telemachus aims to provide for **telematics** what GTFS did for **public transport** — a shared foundation for open mobility data.  
- Provide an **open, simple standard**.  
- Enable **interoperability** across providers.  
- Support both **scientific research** and **business applications**.  

---

## 🔗 Data Flow Overview

```mermaid
graph TD
  Prov[Providers: Geotab · Webfleet · Samsara] --> Core[Telemachus Core v0.2 · Open Pivot Schema]
  Core --> Fleet[Fleet Premium · Missions · KPIs · SLA]
  Core --> Research[Research · Data Science · Simulation]
  Fleet --> Apps[Business Apps · Fleet Mgmt · Insurance]
  Research --> Sci[Scientific Outputs · Publications · Models]
```

## 🔍 Governance and Evolution

The Telemachus Core Specification evolves through RFC proposals, public discussions, and versioned releases as defined in RFC-0011.  
This process ensures transparent governance, community involvement, and continuous improvement of the specification.

## 📖 Citation

If you use Telemachus in research or projects, please cite:

S. Edet (2025). *Telemachus Core Specification (v0.2)*.  
Zenodo. https://doi.org/10.5281/zenodo.17228092  

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17228092.svg)](https://doi.org/10.5281/zenodo.17228092)