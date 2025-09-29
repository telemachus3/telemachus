
# Telemahcus Completeness Score (TCS)

The **Telemachus Completeness Score (TCS)** is a simple metric that measures how complete a provider’s telematics dataset is when mapped to the **Telemachus Core** schema.

---

## Definition

TCS is defined as:

\[
TCS = \frac{\text{Number of Core fields filled}}{\text{Total Core fields}} \times 100
\]

- **Core fields** include GNSS, Motion, Quality, IMU, Engine, Events, Context, Source.  
- Optional fields that are systematically absent are counted as **missing**.  
- Each field is weighted equally in the base definition (weights can be refined later).

---

## Example Calculation

### Case: Geotab
- Provides: position.lat/lon, speed_kph, heading, fuel_pct, odometer_km, events[].type.  
- Misses: IMU, GNSS quality, many engine details.  
- Score ≈ 65%.

### Case: Webfleet
- Provides: lat/lon, speed, odometer, events.  
- Misses: fuel_pct, RPM, IMU, GNSS quality.  
- Score ≈ 55%.

### Case: Samsara
- Provides: lat/lon, speed, heading, rpm, fuel_pct, odometer, satelliteCount.  
- Misses: IMU, detailed quality.  
- Score ≈ 70%.

### Case: RS3 Simulation
- Provides: full GNSS, Motion, IMU, Engine, Events, Context.  
- Score = 100%.

---

## Illustrative Table

| Provider       | Fields present         | Approx. TCS |
|----------------|-----------------------|-------------|
| Geotab         | GPS, speed, fuel, odo, events | ~65% |
| Webfleet       | GPS, speed, odo, events       | ~55% |
| Samsara        | GPS, speed, odo, fuel, rpm, sats | ~70% |
| RS3 Simulation | Full dataset                   | 100% |

---

## Usage

- **Scientific**: Compare data quality across providers.  
- **Business**: Benchmark vendors for fleet KPIs.  
- **Transparency**: Encourage providers to expose more fields.  
- **Future work**: introduce **weighted TCS** (e.g. GPS mandatory, IMU optional) and **frequency factor** (Hz of sampling).  

---