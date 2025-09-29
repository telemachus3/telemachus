# Telemachus Completeness Score (TCS)

The **Telemachus Completeness Score (TCS)** addresses the challenge of fragmentation and uneven data quality in telematics datasets. By providing a standardized metric, TCS helps stakeholders understand how complete a provider’s telematics data is relative to the **Telemachus Core** schema.

---

## Definition

TCS is defined as:

\[
TCS = \frac{\text{Number of Core fields filled}}{\text{Total Core fields}} \times 100
\]

**Note:** TCS measures **field availability** and completeness, not the accuracy or precision of the data provided.

- **Core fields** include GNSS, Motion, Quality, IMU, Engine, Events, Context, Source.  
- Optional fields that are systematically absent are counted as **missing**.  
- Each field is weighted equally in the base definition (weights can be refined later).

---

## Example Calculation

### Case: Geotab
- Provides: position.lat/lon, speed_kph, heading, fuel_pct, odometer_km, events[].type.  
- Misses: IMU, GNSS quality, many engine details.  
- Score ≈ 65%.  
- *Implications:* Suitable for general fleet tracking but limited for advanced analytics requiring IMU or detailed engine diagnostics. According to Geotab's API documentation, fuel and odometer data are reliably available, but IMU data and GNSS quality indicators are absent, restricting the depth of motion analysis and signal quality assessment. [Geotab API Documentation](https://geotab.github.io/sdk/software/guides/api-overview/)

### Case: Webfleet
- Provides: lat/lon, speed, odometer, events.  
- Misses: fuel_pct, RPM, IMU, GNSS quality.  
- Score ≈ 55%.  
- *Implications:* Good coverage of basic GPS data but insufficient for fuel management or driver behavior analysis. Webfleet's API documentation confirms availability of basic GPS coordinates, speed, odometer readings, and some event types, but lacks engine metrics such as RPM and fuel percentage, as well as quality indicators, limiting comprehensive vehicle diagnostics. [Webfleet API Documentation](https://www.webfleet.com/static/help/webfleet-connect/en_gb/index.html)

### Case: Samsara
- Provides: lat/lon, speed, heading, rpm, fuel_pct, odometer, satelliteCount.  
- Misses: IMU, detailed quality.  
- Score ≈ 70%.  
- *Implications:* Stronger engine and satellite info supports better diagnostics, though lacking in motion sensor data. Samsara's API exposes richer telemetry data including RPM, fuel percentage, and satellite count, which surpasses the offerings of Geotab and Webfleet, explaining the higher completeness score and enabling more detailed vehicle performance analysis. [Samsara API Documentation](https://developers.samsara.com/reference/overview)

### Case: RS3 Simulation
- Provides: full GNSS, Motion, IMU, Engine, Events, Context.  
- Score = 100%.  
- *Implications:* Complete dataset ideal as a benchmark or for research-grade applications. The RS3 simulation generates all fields specified in the Teleamachus Core schema, including motion sensors (IMU), engine parameters, and quality metrics, making it uniquely complete and suitable as a gold standard reference.

### Case: Teltonika (device-level, not SaaS)
- Provides: rich GNSS fields (lat/lon, altitude, speed, heading), quality indicators (HDOP, satellite count), and multiple IOs from the CAN bus (fuel level, RPM, battery voltage, ignition state).
- Misses: standardized IMU exposure (accelerometer/gyroscope may be encoded in proprietary IOs but not documented in the same way as Core).
- Score ≈ 80–85% depending on device model and firmware.
- *Implications:* Unlike SaaS B2B providers, Teltonika devices can expose much more granular raw data directly from the hardware, including GNSS quality metrics often missing in cloud APIs. However, decoding requires knowledge of the Teltonika Codec format, and completeness depends on device configuration and IO mapping. [Teltonika Codec Documentation](https://wiki.teltonika-gps.com/view/Codec)

---

## Illustrative Table

| Provider       | Fields present                | Approx. TCS |
|----------------|------------------------------|-------------|
| Geotab         | GPS, speed, fuel, odo, events| ~65%        |
| Webfleet       | GPS, speed, odo, events      | ~55%        |
| Samsara        | GPS, speed, odo, fuel, rpm, sats | ~70%    |
| Teltonika (device) | GPS, quality, odo, fuel, rpm, io | ~80–85% |
| RS3 Simulation | Full dataset                 | 100%        |

### Interpretation

A TCS of 55% indicates good coverage of fundamental GPS fields but suggests missing data critical for detailed research or operational insights. Higher scores reflect richer datasets enabling advanced analytics, while scores near 100% represent comprehensive telematics coverage. These differences in scoring directly reflect the actual API capabilities documented by each provider, rather than subjective weighting or assumptions about data importance. It is important to distinguish between SaaS B2B providers (Geotab, Webfleet, Samsara) and hardware-level solutions like Teltonika, which can provide richer raw telemetry but require device-level integration and decoding.

---

## Usage

- **Scientific**: Compare data quality across providers.  
- **Business**: Benchmark vendors for fleet KPIs.  
- **Transparency**: Encourage providers to expose more fields.  
- **Future work**: introduce **weighted TCS** (e.g. GPS mandatory, IMU optional) and **frequency factor** (Hz of sampling).  
- **Procurement**: Support RFPs with objective scoring.  
- **Simulation**: Benchmark against RS3 simulation baseline.  
- **Policy**: Standardization bodies can use TCS as a KPI.  

---

### References

- Geotab API: https://geotab.github.io/sdk/software/guides/api-overview/  
- Webfleet API: https://www.webfleet.com/static/help/webfleet-connect/en_gb/index.html  
- Samsara API: https://developers.samsara.com/reference/overview  
- Teltonika Codec: https://wiki.teltonika-gps.com/view/Codec

---