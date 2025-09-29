# State of the Art

## Introduction

This section provides an overview of the current landscape of data formats and standards used in the field of telematics and mobility data exchange. Understanding the strengths and limitations of existing formats is essential to position Telemachus effectively and highlight its unique contributions.

## Comparative Overview of Existing Formats

| Feature / Format       | [GTFS](https://developers.google.com/transit/gtfs)                      | [DATEX II](https://datex2.eu/)                 | [NGSI-LD](https://www.etsi.org/standards/ngsi-ld)                  | [Flespi](https://flespi.io/)                   | [Otonomo / High Mobility](https://otonomo.io/)  | [Smartcar](https://smartcar.com/)               | MQTT (lightweight IoT protocol) | NDS.Live (navigation data standard) | SensorThings API (OGC standard) | ISO 15118 (EV charging communication) |
|-----------------------|---------------------------|--------------------------|--------------------------|--------------------------|--------------------------|--------------------------|-----------------------------|-------------------------------|-------------------------------|---------------------------------------|
| Primary Use Case       | Public transit schedules  | Traffic and travel data  | Context information model| IoT data platform        | Automotive data exchange | Automotive API platform  | IoT messaging protocol       | Navigation and map data       | IoT sensor data integration   | EV charging communication            |
| Data Model            | Static and real-time transit data | Traffic management data | Linked data, semantic web | Telemetry and sensor data| Vehicle and mobility data| Vehicle telematics and status| Lightweight publish/subscribe messages | Navigation database schema    | Sensor and observation data   | EV charging session and status        |
| Standardization       | Open standard by Google   | European standard ([ISO TC204](https://www.iso.org/committee/54706.html))        | OMA SpecWorks standard    | Proprietary              | Proprietary              | Proprietary              | OASIS standard                | NDS Association standard      | OGC standard                  | ISO international standard            |
| Data Format           | CSV / JSON                | XML                      | JSON-LD                  | JSON                     | JSON                     | JSON, REST APIs          | Binary/text (MQTT protocol)  | Binary/JSON                  | JSON                        | XML/JSON                            |
| Real-time Support     | Yes                       | Yes                      | Yes                      | Yes                      | Yes                      | Yes                      | Yes                         | Limited                     | Yes                         | Yes                                |
| Semantic Interoperability | Limited               | Moderate                 | High                     | Limited                  | Moderate                 | Limited                  | Limited                     | Moderate                    | High                        | Moderate                           |
| Use in Industry       | Widely adopted in transit | Used by traffic agencies | Used in smart cities      | IoT and telematics       | Automotive OEMs and platforms| Automotive app developers and partners| IoT device communication     | Automotive and navigation providers | Smart city and IoT applications | EV manufacturers and charging stations |

### Telemachus: Open and Extensible by Design

While many existing solutions are either proprietary (e.g., Flespi, Otonomo, Smartcar) or focused on specific domains (e.g., GTFS for transit, DATEX II for traffic), Telemachus is distinguished by its open specification and extensibility. It is designed to be adaptable across domains, enabling innovation and broad interoperability. This openness allows for community-driven evolution and integration with both legacy and emerging mobility systems, setting Telemachus apart from domain-limited or closed solutions.

### Additional Observations

The landscape of telematics and mobility data is characterized by a diversity of ecosystems, including public transit, smart cities, automotive, IoT, and energy sectors. This diversity has led to a proliferation of specialized standards and protocols, each optimized for particular use cases and industries. However, this specialization has also resulted in fragmentation and a lack of unified schemas across providers, which complicates data integration and interoperability. Telemachus offers a promising approach as a bridging layer that can harmonize these disparate data sources, providing a flexible and extensible framework that supports cross-domain interoperability and innovation.

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
- [MQTT Protocol](http://mqtt.org/)
- [NDS.Live Navigation Data Standard](https://nds-association.org/)
- [OGC SensorThings API](http://www.opengeospatial.org/standards/sensorthings)
- [ISO 15118 Standard](https://www.iso.org/standard/55366.html)
