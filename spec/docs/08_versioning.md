


# Versioning Policy

The **Telemachus project** follows a versioning strategy inspired by [Semantic Versioning (SemVer)](https://semver.org/), with adaptations for schema-driven projects.

---

## Semantic Versioning

Version numbers have the format:

```
MAJOR.MINOR.PATCH
```

- **MAJOR** → Breaking changes in the schema or SDKs.  
- **MINOR** → Backward-compatible additions (new fields, new contexts).  
- **PATCH** → Backward-compatible fixes (typos, doc updates, bugfixes).

---

## Core vs Contexts vs Fleet Premium

- **Telemachus Core** (open schema) strictly follows SemVer.  
- **Contexts** (optional enrichments) can evolve more flexibly, as they are namespaced and ignorable.  
- **Fleet Premium** (proprietary KPIs) uses its own release cycle, but aligns with Core for compatibility.

---

## Compatibility and Deprecation

- Once a field is **added** to Core, it is never removed.  
- Deprecated fields are retained until the next **MAJOR** release.  
- Consumers should tolerate **unknown fields** (for forward compatibility).  
- Contexts are always **optional** and can evolve independently.

---

## Example Lifecycle

- **v0.1-alpha** → First alpha (basic GNSS + IMU + CAN + Events).  
- **v0.2** → Add new context types (road genome, weather). Backward-compatible.  
- **v0.3** → Introduce TCS scoring reference. Backward-compatible.  
- **v1.0** → First stable release, with finalized Core spec.  
- **v2.0** → Breaking changes (if Core is significantly restructured).

---

## Conclusion

This versioning policy ensures **stability for integrators** while allowing **innovation and extensibility**.  
Users can confidently adopt Telemachus, knowing that **backward compatibility is preserved** within each MAJOR release series.