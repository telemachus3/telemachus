# Context Extensions (v0.2)

This document specifies **Context Extensions** aligned with [RFC-0004 (Extended FieldGroups)](https://github.com/telemachus3/telemachus-spec/blob/main/rfcs/RFC-0004-extended-fieldgroups-schema.md) and [RFC-0009 (RS3 Integration Pipeline)](https://github.com/telemachus3/telemachus-spec/blob/main/rfcs/RFC-0009-rs3-integration-pipeline.md).

**Telemachus Core v0.2** supports *contexts* as optional extensions for Telemachus v0.2 datasets, referenced by the `context` field at the record level. Contexts enrich telematics records with external data and are designed to be flexible: they can be ignored by simple integrations or fully exploited by advanced pipelines.

Contexts provide a way to incorporate additional information that complements the core telematics data. By adding contextual data, users can gain deeper insights and enhance the value of telematics records for various applications, from scientific research to business analytics.

---

## Version Alignment

This document follows the Telemachus Specification v0.2 and adheres to the governance model defined in [RFC-0011](https://github.com/telemachus3/telemachus-spec/blob/main/rfcs/RFC-0011-versioning-and-governance-policy.md).

---

## Purpose

- Add **external knowledge** to telematics records without modifying the Core schema.  
- Support scientific use cases (e.g., altitude for slope estimation).  
- Support business use cases (e.g., weather impact on delivery performance).  

---

## Example Context Types

### Topography

Topography context provides information about the physical characteristics of the terrain, such as slope and surface type. This data is important for understanding vehicle performance and safety in relation to road conditions.

This context can be populated using data from RS3 curvature studies as described in [RFC-0009](https://github.com/telemachus3/telemachus-spec/blob/main/rfcs/RFC-0009-rs3-integration-pipeline.md) or from external geographic APIs as referenced in [RFC-0005](https://github.com/telemachus3/telemachus-spec/blob/main/rfcs/RFC-0005–adapter-architecture.md).

```json
"context": {
  "topography": {
    "slope_deg": -3.0,
    "surface_type": "asphalt"
  }
}
```

### Weather

Weather context adds environmental conditions like temperature and precipitation. This information is crucial for analyzing how weather impacts driving behavior, vehicle efficiency, and delivery reliability.

Weather data can be integrated from external APIs as outlined in [RFC-0005](https://github.com/telemachus3/telemachus-spec/blob/main/rfcs/RFC-0005–adapter-architecture.md) and incorporated into RS3 pipelines per [RFC-0009](https://github.com/telemachus3/telemachus-spec/blob/main/rfcs/RFC-0009-rs3-integration-pipeline.md).

```json
"context": {
  "weather": {
    "temp_c": 7.5,
    "precip_mm": 0.0
  }
}
```

### Road Genome

The Road Genome context is a conceptual extension that aims to capture detailed geometric and risk-related properties of the road network, such as curve radius, clothoid parameters, and risk indices. This context is related to RS3 curvature studies and may be included in a future RFC as a formal standard.

```json
"context": {
  "road_genome": {
    "curve_radius_m": 120.0,
    "clothoid_k": 0.015,
    "risk_index": "high"
  }
}
```

### Environmental Impact

Environmental Impact context provides data related to vehicle emissions and energy recovery, supporting sustainability analyses and regulatory compliance.

```json
"context": {
  "environmental_impact": {
    "co2_grams": 150.5,
    "energy_recovered_kwh": 1.2
  }
}
```

---

## Extensibility

- Each context is **namespaced** (topography, weather, road_genome, environmental_impact, etc.).  
- New contexts can be added without breaking compatibility.  
- Unrecognized contexts can be safely ignored by consumers.  

---

## Emerging Contexts

- **Emissions:** data related to vehicle emissions and environmental impact.  
- **Driver Behavior:** metrics and indicators of driver performance and habits.  
- **Traffic Conditions:** real-time or historical traffic flow and congestion data.  
- **Maintenance:** information on vehicle maintenance status and schedules.  
- **Urban Context:** data about urban density, speed limits, and infrastructure types, intended to align with open-data sources.  
- **Safety Context:** derived accident risk metrics from historical datasets.  

---

## Governance and Evolution

New context types are proposed as separate RFCs and versioned independently to ensure modularity and flexibility. The governance process follows the guidelines established in [RFC-0011](https://github.com/telemachus3/telemachus-spec/blob/main/rfcs/RFC-0011-versioning-and-governance-policy.md), enabling community-driven evolution of the Telemachus specification and its extensions.

---

## Conclusion

Contexts allow **progressive enrichment** of telematics data.  
They keep the Core schema lightweight, while enabling advanced analytics for research and industry.  
Moreover, contexts can evolve from early prototypes (like the Road Genome) into future standards, providing a flexible framework that bridges raw telematics data with domain-specific knowledge and insights.