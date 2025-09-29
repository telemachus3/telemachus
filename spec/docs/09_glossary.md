

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

## VIN
**Vehicle Identification Number.** A unique 17-character code assigned to every motor vehicle, used for identification and traceability.

## API
**Application Programming Interface.** A set of definitions and protocols for building and integrating application software, enabling communication between different systems.

## SDK
**Software Development Kit.** A collection of software tools, libraries, documentation, and code samples that facilitate the development of applications for a specific platform or standard.

## Parquet
An open-source, columnar storage file format optimized for analytical workloads, providing efficient data compression and encoding schemes.

## JSON / JSONL
**JSON (JavaScript Object Notation):** A lightweight, text-based data interchange format that is easy for humans to read and write, and for machines to parse and generate.
**JSONL (JSON Lines):** A format where each line is a valid JSON object, commonly used for streaming large datasets.

## CSV
**Comma-Separated Values.** A simple file format used to store tabular data, where each line represents a data record and each value is separated by a comma.

## Semantic Interoperability
The ability of computer systems to exchange data with unambiguous, shared meaning, ensuring that the precise meaning of exchanged information is understood by all parties.

## Standardization Bodies (CEN, ISO, OGC)
Organizations responsible for developing and maintaining standards:
- **CEN:** European Committee for Standardization.
- **ISO:** International Organization for Standardization.
- **OGC:** Open Geospatial Consortium.

## Fleet Management System (FMS)
A platform or software solution used to manage, monitor, and coordinate vehicles, drivers, and operations in a fleet, often integrating telematics data.

## Digital Twin
A virtual representation of a physical asset, system, or process, updated with real-time data to enable simulation, analysis, and monitoring.

## Edge Computing
Distributed computing paradigm that brings computation and data storage closer to the location where it is needed, improving response times and saving bandwidth, particularly relevant for IoT and telematics.

## MQTT
**Message Queuing Telemetry Transport.** A lightweight, publish-subscribe network protocol designed for constrained devices and low-bandwidth, high-latency, or unreliable networks, widely used in IoT applications.