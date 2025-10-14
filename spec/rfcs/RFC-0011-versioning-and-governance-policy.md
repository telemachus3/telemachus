---
RFC: 0011
Title: Versioning and Governance Policy
Version: 0.1-draft
Status: Draft
Author: Sébastien Edet
Date: 2025-10-13
Project: Telemachus Specification
---

## 1. Purpose

This RFC establishes the **versioning model, governance process, and RFC lifecycle** for the Telemachus Specification.  
It defines how changes to schemas, datasets, and validation tools are proposed, reviewed, approved, and released.  
The goal is to ensure transparent evolution, backward compatibility, and traceable decision-making across the Telemachus ecosystem.

---

## 2. Scope

This policy applies to:
- All RFC documents under `rfcs/`
- All schemas under `schema/`
- All dataset specifications and validation tools
- Any public release of the Telemachus specification or supporting software

It does **not** cover individual project management or internal code changes unrelated to the published specification.

---

## 3. Governance Principles

Telemachus governance follows three guiding principles:
1. **Transparency** — All decisions are documented via RFCs.  
2. **Backward Compatibility** — No breaking changes within the same major version.  
3. **Reproducibility** — All releases are traceable to specific RFCs and commits.

---

## 4. Specification Lifecycle

The Telemachus Specification evolves through iterative RFCs that are grouped into official **specification releases** (`v0.2`, `v0.3`, etc.).  
Each release aggregates multiple RFCs once they reach the `Released` status.

| Stage         | Description                                   |
|--------------|-----------------------------------------------|
| **Draft**    | Initial proposal under discussion.             |
| **Accepted** | Approved conceptually after review.            |
| **Implemented** | Supported by code, schema, or dataset updates. |
| **Released** | Included in an official spec release.          |
| **Deprecated** | Replaced by newer RFCs or retired.           |

---

## 5. Versioning Model

Telemachus uses **Semantic Versioning (SemVer)** for all specification and software components.

| Version   | Meaning                                         |
|-----------|-------------------------------------------------|
| `MAJOR`   | Incompatible schema or API changes              |
| `MINOR`   | Backward-compatible additions or improvements   |
| `PATCH`   | Bug fixes, clarifications, or documentation updates |

Example:  
- `0.2.0` → initial stable version with Extended FieldGroups  
- `0.3.0` → adds Dataset Spec and Validation Framework  
- `1.0.0` → first long-term stable release  

---

## 6. Relationship Between RFCs and Releases

Each specification release corresponds to a **bundle of RFCs**:

| Release | RFCs Included                | Highlights                        |
|---------|-----------------------------|-----------------------------------|
| **v0.2** | RFC-0001, RFC-0002, RFC-0004 | Core schema + Extended FieldGroups |
| **v0.3** | RFC-0003, RFC-0005, RFC-0007 | Dataset Spec + Adapters + Validation |
| **v0.4** | RFC-0008, RFC-0011           | Ontology + Governance             |
| **v1.0** | RFC-0009, RFC-0017, RFC-0026 | RS3 Integration + Road Genome + Community |

---

## 7. RFC Workflow

### 7.1 Creation
- RFCs are created under `rfcs/` as Markdown files: `RFC-XXXX-title.md`
- Each RFC must include:
  - YAML header metadata  
  - Number, title, author, date  
  - Purpose, scope, and numbered sections  
  - References to dependent RFCs  

### 7.2 Review and Approval
- RFCs are reviewed via GitHub Pull Requests.  
- Reviewers comment inline; authors update the draft.  
- Once consensus is reached, the RFC moves to `Accepted`.

### 7.3 Implementation
- Implementation must include:
  - Schema or code changes in a referenced repository  
  - Validation tests or dataset examples  
- The RFC is marked `Implemented` once code merges into `main`.

### 7.4 Release
- A release occurs when multiple `Implemented` RFCs form a coherent milestone.  
- Version numbers and changelogs are updated accordingly.  
- Released RFCs are frozen and cannot be modified (only superseded).

---

## 8. Backward Compatibility Policy

To maintain stability:
- No breaking schema changes within the same `MAJOR` version.  
- Deprecated fields must remain valid for at least one `MINOR` release.  
- Validation tools must support older schemas within the same major version.  
- Major migrations (e.g., v0.x → v1.0) require explicit migration guides.

---

## 9. Deprecation Process

When a field, schema, or behavior becomes obsolete:
1. It is marked as `deprecated` in the schema.  
2. The corresponding RFC is updated with a note and deprecation date.  
3. A new RFC supersedes it.  
4. The change is communicated in the next release notes.

---

## 10. RFC Numbering and Naming

- RFCs are numbered sequentially (0001, 0002, …).  
- File naming convention:  
  ```
  rfcs/RFC-XXXX-short-title.md
  ```  
- Titles use lowercase kebab case; inside the file, the full title is capitalized.  
- Numbers are never reused, even for deprecated or withdrawn RFCs.

---

## 11. Changelog and Tracking

A file `rfcs/STATUS.yml` (or `ROADMAP.md`) tracks all RFCs with their status, author, and release association.

Example:
```yaml
- id: 0001
  title: Telemachus Core 0.2
  status: Released
  included_in: v0.2
- id: 0003
  title: Dataset Specification
  status: Accepted
  target_release: v0.3
```

This registry acts as the canonical index for the entire specification history.

---

## 12. Governance Roles

| Role             | Responsibility                                  |
|------------------|-------------------------------------------------|
| **Editor**       | Maintains consistency and formatting of RFCs     |
| **Reviewer**     | Evaluates RFCs for technical and conceptual validity |
| **Maintainer**   | Oversees schema and code implementation          |
| **Release Manager** | Approves and tags official specification versions |

Multiple roles can be held by the same person in early stages.

---

## 13. Community Contributions

Telemachus encourages community RFCs and discussion through:
- GitHub Issues (`discussion` label)
- Pull Requests with draft RFCs
- Public feedback during review cycles

Contributors must follow the RFC template and licensing terms (AGPL for core, MIT for adapters).

---

## 14. Release Publication

Each release must include:
- Tag on GitHub (`v0.x.y`)
- Generated documentation on GitHub Pages
- Updated changelog linking all included RFCs
- Archived snapshot (Zenodo DOI when relevant)

---

## 15. Future Governance Improvements

Planned improvements include:
- Integration with the OpenTelemetry governance model  
- RFC voting or review committee system  
- Automated validation of RFC metadata (YAML headers)  
- Public roadmap visualization and dashboard  

---

## 16. References

- RFC-0001 — *Telemachus Core 0.2*  
- RFC-0002 — *Comparative Telematics API Formats*  
- RFC-0003 — *Dataset Specification 0.2*  
- RFC-0007 — *Validation Framework & CLI Rules*  
- Semantic Versioning — https://semver.org/  
- OpenTelemetry Governance — https://github.com/open-telemetry/community  

---

## 17. Conclusion

This RFC defines the governance backbone for Telemachus, ensuring transparent, reproducible, and collaborative evolution of the specification.  
It establishes the link between RFCs, implementation, and releases — providing the structure necessary for Telemachus to mature into a stable, open standard for mobility and telemetry data.