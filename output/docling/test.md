## Key interfaces

- Sensor input: Pt1000, four-wire connection
- Power input: 24 V DC nominal, 6 A maximum
- Data interface: isolated RS-485 at 115200 bit/s

## 3. Control model

The expected steady-state heat balance is expressed by Q = m * c\_p * Delta T . Controller efficiency is calculated as eta = P\_load / P\_input .

## Engineering note

Measurements are valid only after the plate-temperature slope remains below 0.1 degrees C per minute for five consecutive minutes.

## Thermal Control Module

## Verification Test Specification

| Document ID   | TS-042              | Revision       | 1.3                   |
|---------------|---------------------|----------------|-----------------------|
| Status        | Released            | Test date      | 2026-08-07            |
| Owner         | Systems Engineering | Classification | Internal test fixture |

## 1. Scope

This specification defines the bench tests for a 24 V closed-loop thermal control module. The module regulates an aluminium test plate between 20 and 80 degrees C while reporting temperature, supply current, and fault status.

## 2. System overview

The test article contains three functional blocks. Their signal flow is shown below; arrows indicate the intended reading direction from left to right.

Figure 1 - Closed-loop thermal control signal path

<!-- image -->

## 4. Performance measurements

Table 1 contains the reference measurements captured at five operating points. Numeric values use SI-compatible units and a decimal point.

Table 1 - Thermal performance at nominal supply voltage

| Test point   |   Ambient (deg C) |   Input (V) |   Load (A) |   Plate (deg C) |   Efficiency (%) |
|--------------|-------------------|-------------|------------|-----------------|------------------|
| TP-01        |              20.1 |       24.02 |       1.20 |            30.0 |             91.2 |
| TP-02        |              20.0 |       24.01 |       2.35 |            40.0 |             92.8 |
| TP-03        |              22.4 |       23.98 |       3.60 |            55.0 |             93.5 |
| TP-04        |              25.2 |       23.96 |       4.80 |            70.0 |             92.9 |
| TP-05        |              25.0 |       23.94 |       5.50 |            80.0 |             91.7 |

## 5. Verification procedure

1. Inspect the wiring and confirm protective-earth continuity.
2. Apply 24 V DC with the current limit set to 6 A.
3. Command each plate-temperature setpoint in ascending order.
4. Wait for the stability condition defined in Section 3.
5. Record voltage, current, plate temperature, and fault status.

## 6. Acceptance criteria

| Requirement       | Limit          | Result                               |
|-------------------|----------------|--------------------------------------|
| Temperature error | +/- 1.0 deg C  | Pass if every point complies         |
| Input voltage     | 23.5 to 24.5 V | Pass if no dropout occurs            |
| Efficiency        | >= 90.0%       | Pass if measured after stabilization |
| Communication     | 0 frame errors | Pass over 10,000 frames              |

## 7. Expected reading order

A correct conversion reads Sections 4 through 7 in sequence, keeps each table row intact, and places this final paragraph after the acceptance table.