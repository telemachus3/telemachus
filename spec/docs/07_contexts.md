

# Context Extensions

**Telemachus Core** supports *contexts* as optional extensions to enrich telematics records with external data.  
Contexts are designed to be flexible: they can be ignored by simple integrations, or fully exploited by advanced pipelines.

---

## Purpose

- Add **external knowledge** to telematics records without modifying the Core schema.  
- Support scientific use cases (e.g. altitude for slope estimation).  
- Support business use cases (e.g. weather impact on delivery performance).  

---

## Example Context Types

### Topography
```json
"context": {
  "topography": {
    "slope_deg": -3.0,
    "surface_type": "asphalt"
  }
}
```

### Weather
```json
"context": {
  "weather": {
    "temp_c": 7.5,
    "precip_mm": 0.0
  }
}
```

### Road Genome
```json
"context": {
  "road_genome": {
    "curve_radius_m": 120.0,
    "clothoid_k": 0.015,
    "risk_index": "high"
  }
}
```

---

## Extensibility

- Each context is **namespaced** (topography, weather, road_genome, etc.).  
- New contexts can be added without breaking compatibility.  
- Unrecognized contexts can be safely ignored by consumers.  

---

## Conclusion

Contexts allow **progressive enrichment** of telematics data.  
They keep the Core schema lightweight, while enabling advanced analytics for research and industry.