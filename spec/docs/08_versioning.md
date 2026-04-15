# Versioning and Governance Policy (v0.2)

This versioning policy, as defined in RFC-0011, governs all Telemachus schemas, datasets, contexts, and adapters, ensuring a consistent and transparent approach to version management across the ecosystem.

---

## Version Alignment

This document follows Telemachus Spec v0.2 and defines governance principles for all future versions (v0.3+), providing a framework for evolution and compatibility.

---

## Semantic Versioning

Version numbers have the format:

```
MAJOR.MINOR.PATCH
```

- **MAJOR** → Breaking changes in the schema or SDKs, validated through a dedicated RFC proposal and accepted by governance following the RFC-0011 process.  
- **MINOR** → Backward-compatible additions (new fields, new contexts).  
- **PATCH** → Backward-compatible fixes (typos, doc updates, bugfixes).

---

## Scope of Versioning

- **Core** (open schema) strictly follows SemVer and represents the foundational data model.  
- **Contexts** (optional modules) are governed by RFC-0004, allowing flexible evolution while maintaining compatibility.  
- **Fleet Premium** (proprietary KPIs and features) uses its own release cycle but aligns versioning with Core for compatibility.  
- **Adapters** (industrial connectors) are governed by RFC-0005, ensuring standardized integration points.

---

## Compatibility and Deprecation

- Once a field is **added** to Core, it is never removed.  
- Deprecated fields are retained until the next **MAJOR** release.  
- Consumers should tolerate **unknown fields** (for forward compatibility).  
- Contexts are always **optional** and can evolve independently.

---

## Governance Workflow

- **Proposal via RFC:** Changes are proposed through an RFC document progressing from Draft to Discussion and finally Accepted status.  
- **Implementation and Validation:** Accepted RFCs are implemented and validated in compliance with RFC-0007.  
- **Release and Version Tagging:** Releases follow SemVer rules, with version tags reflecting the nature of changes.  
- **Publication:** All releases and changelogs are published on GitHub Pages for transparency.

---

## Example Lifecycle

- **v0.1-alpha** → Initial Core release (RFC-0001).  
- **v0.2** → Addition of Datasets, Adapters, and Validation mechanisms (RFCs 0003–0007).  
- **v0.3** → RS3 integration and TCS metrics introduction (RFCs 0009–0006).  
- **v1.0** → Governance framework finalized and enforced (RFC-0011).

---

## Governance and Transparency

The Telemachus project adopts an RFC-driven governance approach to ensure transparency, inclusiveness, and stability. Community members are encouraged to participate in discussions and proposals via the public repository at [https://github.com/telemachus3/telemachus-spec/discussions](https://github.com/telemachus3/telemachus-spec/discussions).