# Roadmap

This roadmap follows the RFC governance model described in [RFC-0011](https://github.com/telemachus/specifications/blob/main/rfcs/0011-governance.md).

---

## Phase 1 – Short-Term (v0.2 Development, 0–3 months)

- ✅ Release **v0.1-alpha** with GNSS, Motion, IMU, Engine, Events, Context, Source.
- Publish RFCs 0001–0011 to define core specifications and governance.
- Launch the RFC Discussions board on GitHub to engage the community.
- Expand documentation (State of the Art, Mappings, TCS, Contexts, Versioning, Glossary).
- Add more provider mappings (Geotab, Webfleet, Samsara, Teltonika).
- Deliver Python SDK (`telemachus-py`) with DataFrame + Parquet support.
- Deliver CLI tool (`telemachus-cli`) with validation and conversion commands.
- Publish example datasets (RS3 simulation, provider samples).
- Publish RS3 simulation datasets in Telemachus format (JSON/Parquet).
- Add "Getting Started" tutorials for SDK and CLI in the documentation.

---

## Phase 2 – Medium-Term (v0.3–v0.9 Consolidation, 3–12 months)

- Release **v0.2–v0.9** with incremental improvements.
- Emphasize validation enhancements as per [RFC-0007](https://github.com/telemachus/specifications/blob/main/rfcs/0007-validation.md).
- Integrate RS3 baseline datasets following [RFC-0009](https://github.com/telemachus/specifications/blob/main/rfcs/0009-rs3-integration.md).
- Roll out governance processes defined in [RFC-0011](https://github.com/telemachus/specifications/blob/main/rfcs/0011-governance.md).
- Add **Telemachus Completeness Score (TCS)** reference implementation.
- Expand **context modules**: altitude IGN, weather ERA5, road genome.
- Develop **bindings** for other languages (Java, JS/TS).
- Engage first adopters (researchers, SSII, mobility players).
- Publish **white paper** and present at industry/scientific conferences.
- Register DOI (Zenodo) for citation and adoption in academia.
- Provide official RS3 baseline dataset with TCS = 100% as reference.
- Publish benchmark comparing SaaS providers (Geotab, Webfleet, Samsara) vs RS3 baseline.
- Submit first scientific paper or extended abstract to an academic venue.
- Release Telemachus Datasets v1.0.
- Publish RS3 ↔ Provider dataset comparison.

---

## Phase 3 – Long-Term (v1.0 Standardization, 12+ months)

- Release **v1.0 stable** with frozen Core spec.
- Define **Fleet Premium** extension: missions, SLA, KPIs.
- Promote adoption as an **open industry standard** (like GTFS).
- Align with standardization bodies (ISO, OGC, CEN).
- Create Telemachus Working Group for community governance.
- Formalize governance charter under [RFC-0011](https://github.com/telemachus/specifications/blob/main/rfcs/0011-governance.md).
- Integrate with ecosystem: insurance, fleet management, smart city.
- Build **community governance model** (open RFC process).
- Explore integration with **Otonomo/High Mobility/Flespi** and OEM APIs.
- Internationalization: documentation in FR/EN and wider community engagement.
- Formalize Road Genome context into a structured module (if adopted).
- Establish partnerships with standardization bodies (ISO, OGC, CEN).
- Provide certification or compliance badge for adopters.

---

## RFC Alignment Overview

- **Phase 1** focuses on establishing the foundational specifications and governance through RFCs 0001–0011, setting the stage for community engagement and initial tooling.
- **Phase 2** centers on validation improvements (RFC-0007), RS3 dataset integration (RFC-0009), and governance rollout (RFC-0011), alongside dataset releases and ecosystem expansion.
- **Phase 3** targets stable core specification release (v1.0), formal standardization, governance institutionalization, and broader industry adoption aligned with recognized standards bodies.

---

## Conclusion

Telemachus will evolve from a **research-backed schema** into an **open industry standard** through an RFC-driven governance model, ensuring both scientific credibility and business relevance.  
This staged roadmap, anchored in formal RFCs, ensures stability, community participation, and long-term sustainability.