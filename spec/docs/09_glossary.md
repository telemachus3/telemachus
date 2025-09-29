

# Glossary

This glossary defines key terms used throughout the **Telemachus** documentation.

---

## GNSS
**Global Navigation Satellite System.** Generic term for satellite-based positioning systems (GPS, Galileo, GLONASS, BeiDou).

## GPS
**Global Positioning System.** The US GNSS constellation, often used as a synonym for satellite navigation.

## HDOP / VDOP / PDOP
**Dilution of Precision.**  
- HDOP = Horizontal DOP  
- VDOP = Vertical DOP  
- PDOP = Position DOP (combined)  
Lower values indicate better positioning accuracy.

## IMU
**Inertial Measurement Unit.** A device measuring acceleration, angular velocity, and sometimes magnetic field.  
Used for dead reckoning, motion tracking, and stability.

### Accelerometer
Measures acceleration in m/s² along X, Y, Z axes.

### Gyroscope
Measures angular velocity in rad/s around X, Y, Z axes.

### Magnetometer
Measures magnetic field strength (µT), used for compass orientation.

## CAN
**Controller Area Network.** A vehicle bus standard enabling communication between electronic control units (ECUs).

## OBD-II
**On-Board Diagnostics II.** Standardized interface (mainly in cars) for accessing diagnostic trouble codes and live engine parameters.

## Event (Telematics)
Discrete driving or vehicle event detected by a device or provider, e.g. harsh braking, speeding, geofence entry.

## GTFS
**General Transit Feed Specification.** Open standard for describing public transport schedules and routes. Inspiration for Telemachus as an open mobility format.

## DATEX II
European standard (CEN) for traffic and travel data exchange. XML-based, complex but widely adopted.

## NGSI-LD
Open standard for context data exchange, based on JSON-LD. Used in smart city and IoT projects.

## TCS
**Telemachus Completeness Score.** A metric introduced by Telemachus to evaluate how complete a provider’s dataset is relative to the Core schema.