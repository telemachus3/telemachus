# State of the Art

## Introduction

This section provides an overview of the current landscape of data formats and standards used in the field of telematics and mobility data exchange. Understanding the strengths and limitations of existing formats is essential to position Telemachus effectively and highlight its unique contributions.

## Comparative Overview of Existing Formats

| Feature / Format       | [GTFS](https://developers.google.com/transit/gtfs)                      | [DATEX II](https://datex2.eu/)                 | [NGSI-LD](https://www.etsi.org/standards/ngsi-ld)                  | [Flespi](https://flespi.io/)                   | [Otonomo / High Mobility](https://otonomo.io/)  | [Smartcar](https://smartcar.com/)               |
|-----------------------|---------------------------|--------------------------|--------------------------|--------------------------|--------------------------|--------------------------|
| Primary Use Case       | Public transit schedules  | Traffic and travel data  | Context information model| IoT data platform        | Automotive data exchange | Automotive API platform  |
| Data Model            | Static and real-time transit data | Traffic management data | Linked data, semantic web | Telemetry and sensor data| Vehicle and mobility data| Vehicle telematics and status|
| Standardization       | Open standard by Google   | European standard ([ISO TC204](https://www.iso.org/committee/54706.html))        | OMA SpecWorks standard    | Proprietary              | Proprietary              | Proprietary              |
| Data Format           | CSV / JSON                | XML                      | JSON-LD                  | JSON                     | JSON                     | JSON, REST APIs          |
| Real-time Support     | Yes                       | Yes                      | Yes                      | Yes                      | Yes                      | Yes                      |
| Semantic Interoperability | Limited               | Moderate                 | High                     | Limited                  | Moderate                 | Limited                  |
| Use in Industry       | Widely adopted in transit | Used by traffic agencies | Used in smart cities      | IoT and telematics       | Automotive OEMs and platforms| Automotive app developers and partners|

### Telemachus: Open and Extensible by Design

While many existing solutions are either proprietary (e.g., Flespi, Otonomo, Smartcar) or focused on specific domains (e.g., GTFS for transit, DATEX II for traffic), Telemachus is distinguished by its open specification and extensibility. It is designed to be adaptable across domains, enabling innovation and broad interoperability. This openness allows for community-driven evolution and integration with both legacy and emerging mobility systems, setting Telemachus apart from domain-limited or closed solutions.

## Conclusion

Telemachus aims to build upon the strengths of existing standards by providing a flexible, interoperable, and extensible framework tailored to the needs of modern telematics applications. By integrating semantic richness with real-time capabilities and broad industry applicability, Telemachus positions itself as a versatile solution bridging gaps left by current formats.


## References

- [GTFS Official Documentation](https://developers.google.com/transit/gtfs)
- [DATEX II Official Website](https://datex2.eu/)
- [NGSI-LD Specification by ETSI](https://www.etsi.org/standards/ngsi-ld)
- [Flespi IoT Platform](https://flespi.io/)
- [Otonomo Automotive Data Platform](https://otonomo.io/)
- [High Mobility Developer Portal](https://high-mobility.com/)
- [Smartcar Platform](https://smartcar.com/)
- [ISO TC204: Intelligent transport systems](https://www.iso.org/committee/54706.html)
