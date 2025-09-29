# Context Extensions

**Telemachus Core** supports *contexts* as optional extensions to enrich telematics records with external data.  
Contexts are designed to be flexible: they can be ignored by simple integrations, or fully exploited by advanced pipelines.

Contexts provide a way to incorporate additional information that complements the core telematics data. By adding contextual data, users can gain deeper insights and enhance the value of telematics records for various applications, from scientific research to business analytics.

---

## Purpose

- Add **external knowledge** to telematics records without modifying the Core schema.  
- Support scientific use cases (e.g. altitude for slope estimation).  
- Support business use cases (e.g. weather impact on delivery performance).  

---

## Example Context Types

### Topography

Topography context provides information about the physical characteristics of the terrain, such as slope and surface type. This data is important for understanding vehicle performance and safety in relation to road conditions.

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

```json
"context": {
  "weather": {
    "temp_c": 7.5,
    "precip_mm": 0.0
  }
}
```

### Road Genome

The Road Genome context is a conceptual extension that aims to capture detailed geometric and risk-related properties of the road network, such as curve radius, clothoid parameters, and risk indices. This context is still a concept/idea and not yet a formal standard. Future developments could include additional parameters like lane width, surface friction, and traffic signage information.

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

## Additional Potential Contexts

- Emissions: data related to vehicle emissions and environmental impact.  
- Driver Behavior: metrics and indicators of driver performance and habits.  
- Traffic Conditions: real-time or historical traffic flow and congestion data.  
- Maintenance: information on vehicle maintenance status and schedules.  

---

## Conclusion

Contexts allow **progressive enrichment** of telematics data.  
They keep the Core schema lightweight, while enabling advanced analytics for research and industry.  
Moreover, contexts can evolve from early prototypes (like the Road Genome) into future standards, providing a flexible framework that bridges raw telematics data with domain-specific knowledge and insights.