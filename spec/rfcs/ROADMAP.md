
> **Sub-roadmap Telemachus spec (RFCs).** For the cross-project commercial deployment
> view, see [`../../ROADMAP.md`](../../ROADMAP.md). For IP/publication
> logic, see [`../../WORKFLOW.md`](../../WORKFLOW.md).

# Telemachus RFC Roadmap (2024)

This roadmap presents the structured development of Telemachus as a data modeling and interoperability specification. It is organized into four major tracks: Core Specification, Interoperability & Tooling, Research & Extended Applications, and Governance & Future Track. The RFCs listed here reflect the current, consolidated scope—datasets, fieldgroups, adapters, validation, RS3, and governance. Protocol-level RFCs are out of scope for Telemachus.

---

## I. CORE SPECIFICATION

| RFC   | Title                                 | Description                                                      | Target Release |
|-------|---------------------------------------|------------------------------------------------------------------|---------------|
| 0001  | Telemachus Data Model Fundamentals    | Core concepts: datasets, fields, fieldgroups, units, metadata    | v0.2          |
| 0003  | Fieldgroups & Composition             | Fieldgroup definitions, composition, reuse, inheritance          | v0.3          |
| 0004  | Dataset Schema & Validation           | Dataset schema format, constraints, validation rules             | v0.3          |
| 0005  | Adapters & Mapping                    | Adapter system for mapping to/from external representations      | v0.4          |
| 0007  | Reference Set 3 (RS3) Integration     | RS3 dataset and fieldgroup mapping, compatibility                | v0.5          |
| 0009  | Extended Types & Units                | Support for custom types, units, and extensibility mechanisms    | v0.6          |

---

## II. INTEROPERABILITY & TOOLING

| RFC   | Title                                 | Description                                                      | Target Release |
|-------|---------------------------------------|------------------------------------------------------------------|---------------|
| 0011  | Validation Tooling & Reference Suite  | Canonical validation tools, conformance suite, CLI/SDKs          | v0.7          |

---

## III. RESEARCH & EXTENDED APPLICATIONS

| RFC   | Title                                 | Description                                                      | Target Release |
|-------|---------------------------------------|------------------------------------------------------------------|---------------|
| (TBD) | Extended Domains & Experimental Apps  | Applying Telemachus to novel or domain-specific use cases        | v1.0+         |

---

## IV. GOVERNANCE & FUTURE TRACK

| RFC   | Title                                 | Description                                                      | Target Release |
|-------|---------------------------------------|------------------------------------------------------------------|---------------|
| (TBD) | Governance Process & Community        | RFC process, change management, working groups                   | v1.0          |

---

## Roadmap Summary Table

| Track                               | RFCs                | Status      |
|--------------------------------------|---------------------|-------------|
| **Core Specification**               | 0001, 0003, 0004, 0005, 0007, 0009 | [ ] Planned |
| **Interoperability & Tooling**       | 0011                | [ ] Planned |
| **Research & Extended Applications** | (TBD)               | [ ] Planned |
| **Governance & Future Track**        | (TBD)               | [ ] Planned |

---

## Roadmap Diagram (Mermaid)

```mermaid
graph TD
    CS[Core Specification]
    CS1[RFC-0001: Data Model Fundamentals]
    CS3[RFC-0003: Fieldgroups & Composition]
    CS4[RFC-0004: Dataset Schema & Validation]
    CS5[RFC-0005: Adapters & Mapping]
    CS7[RFC-0007: RS3 Integration]
    CS9[RFC-0009: Extended Types & Units]
    CS --> CS1
    CS1 --> CS3
    CS3 --> CS4
    CS4 --> CS5
    CS5 --> CS7
    CS7 --> CS9

    IT[Interoperability & Tooling]
    IT11[RFC-0011: Validation Tooling & Suite]
    IT --> IT11
    CS9 --> IT11

    RE[Research & Extended Applications]
    RE0[TBD: Extended Domains & Experimental]
    RE --> RE0
    IT11 --> RE0

    GV[Governance & Future Track]
    GV0[TBD: Governance & Community]
    GV --> GV0
    RE0 --> GV0
```
