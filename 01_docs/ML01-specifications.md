# ML01 PROJECT – SPECIFICATIONS
The ML01 project is an electronic system based on a **Raspberry Pi Pico 2W**.  
Its main role is to control **16 yellow LEDs** using 2 buttons and a lightweight embedded web interface using the Microdot framework.  
All components are Through-Hole Technology (THT) and require assembly onto a printed circuit board (DIY).  
<br>
⚠️ **LIMITATIONS AND WARNINGS** ⚠️
- **Indoor use only**
- **Not CE/FCC certified** | Hobbyist/educational use only
- **DIY assembly required** | Soldering skills necessary
- **Open PCB design** | Avoid contact with conductive materials
- **ESD sensitive** | Handle with antistatic precautions
- **No over-voltage protection** beyond PTC fuse
- **Wi-Fi stability** depends on local environment and interference
- **Safety Precautions while the device is powered:** *Thank you for reading the details at the end of this document.*

**The following guides are provided in separate documentation files:**
- [Assembly guide](01_docs/ML01-assembly.md)  
- [Settings guide](01_docs/ML01-settings.md)  
- [Usage guide](01_docs/ML01-usages.md)
---

## A. FUNCTIONS
### A1. LED modes by default
- **FULL mode:** all 16 LEDs ON continuously
- **CHASE mode:** dynamic LED animation sequence synchromnized with Time NTP server
- **OFF mode:** all LEDs OFF
*This open source project allows you to completely reprogram the microcontroller according to your needs.*

### A2. User Button Actions
**Button 1:**
- Short press: cycle through modes → FULL → CHASE → OFF
- Long press: stop script execution
**Button 2:**
- Long press: system reboot

### A3. Web Interface (Microdot):
- Lightweight HTTP server running on Raspberry Pi Pico 2W
- Default port: **5000**
- Provides remote access to LED modes, system status, and log viewing-exporting
- Requires Wi-Fi connection (SSID/password configured in firmware)
---


## B. HARDWARE
### B1. Main Controller: 1× Raspberry Pi Pico 2W RP2350 (THT variant)
- Handles GPIO control, timing, LED driving logic, and web server
- Powered via VSYS (pin 39) from external PSU or USB

### B2. Output Driving: 2× TPIC6B595N power shift registers
- 8 open-drain DMOS outputs per chip
- Up to 150 mA continuous current per output
- Daisy-chain capable (SER OUT → SER IN)
- VCC: +5V, logic-compatible with 3.3V GPIO

### B3. Optoelectronics: 16× yellow LEDs
- High efficiency
- Low power consumption
- Dimension: 5mm round standard
- Brightness: 2500 mcd typical
- Viewing angle: 60°
- Forward voltage: 1.9 to 2.3V typical
- Maximum forward current: 30 mA

### B4. User Input: 2× push buttons (6×6 mm, 1.6 N travel)
- Button 1: GPIO 4 (mode cycling + system stop on long press)
- Button 2: GPIO 5 (system reboot on long press)
- Internal pull-ups enabled in firmware

### B5. Power Conditioning
**16× 160 Ω metal-film resistors (1% 0.6 W):**
- Current limiting for LEDs (~18 mA per LED)

**7× 100 nF ceramic capacitors (X7R, 10% tolerance):**
- 1× per TPIC6B595N
- 4× near LED clusters
- 1× parallel to main electrolytic capacitor

**1× 100 µF electrolytic capacitor (Ø6.30 mm, H11.20 mm):**
- Main power input filtering (+5V to GND)

**1× resettable PTC fuse (Bourns MF-R050):**
- Hold current: 0.5 A
- Trip current: 1.0 A
- Max voltage: 30 V
- Power rating: 750 mW
- Resistance: 770 mΩ

### B6. Power Input
| Parameter           | Value                                       |
|---------------------|---------------------------------------------|
| Voltage             | 5.1 V DC                                    |
| Current (FULL mode) | ~300 mA (1.5 W)                             |
| Current (OFF mode)  | ~50 mA (0.25 W)                             |
| Protection          | PTC resettable fuse (0.5 A hold / 1 A trip) |

### B7. Power Supply: 1x Raspberry Pi 12.7W Micro USB
- AC 100-240V 50/60Hz input
- DC 5.1V 2.5A output
- 12.7W maximum output power
- 1.5m 18AWG captive cable
- Micro USB output connector
- Available only with EU power socket
- White color
*Can alternatively be powered via USB port from computer*

### B8. LED Driving
- Open-drain low-side switching via TPIC6B595
- LED anodes connected to +5 V
- LED cathodes connected to TPIC DRAIN outputs through 160 Ω resistors
- LED current per channel: ~18 mA @ 5V supply
- Calculation: (5V - 2.1V Vf) / 160Ω ≈ 18 mA

### B9. Decoupling Strategy
- 1x 100 nF ceramic capacitor on each TPIC6B595N (VCC to GND)
- 4× 100 nF ceramic capacitors distributed near LED clusters
- 1× 100 nF ceramic capacitor in parallel with electrolytic capacitor at main power input
- 1x 100 µF electrolytic capacitor in parallel with ceramic capacitor at main power input

### B10. PCB Specifications
| Property           | Value              |
|--------------------|--------------------|
| Dimensions         | 165 × 110 mm       |
| Thickness          | 1.6 mm             |
| Layer Count        | 2                  |
| Copper Weight      | 1 oz (35 µm)       |
| Surface Finish     | HASL lead-free     |
| Solder Mask Color  | Green              |
| Component Mounting | Through-Hole (THT) |
---


## C. WIRING
### C1. GPIO Pin Mapping for Raspberry Pi Pico 2W
| GPIO Pin | Function            | Connection                  |
|----------|---------------------|-----------------------------|
| GPIO 4   | Button 1 Input      | Push button (active LOW)    |
| GPIO 5   | Button 2 Input      | Push button (active LOW)    |
| GPIO 7   | TPIC SER IN         | Serial data to first TPIC   |
| GPIO 8   | TPIC RCK            | Register clock (both)       |
| GPIO 9   | TPIC SRCK           | Shift register clock (both) |

### C2. TPIC6B595N Pin Mapping
**First TPIC (chain input)**
| Pin                    | Connection                               |
|------------------------|------------------------------------------|
| Pin 1, 20              | Not used                                 |
| Pin 2 (VCC)            | +5V (Pico pin 39, VSYS)                  |
| Pin 3 (SER IN)         | Pico GPIO 7                              |
| Pins 4-7(DRAIN 0-3)    | LED cathodes via 160Ω resistors          |
| Pin 8 (SRCLR)          | +5V (reset disabled, always HIGH)        |
| Pin 9 (G)              | GND (outputs always enabled, active LOW) |
| Pin 10, 11, 19 (GND)   | Pico GND (pin 3)                         |
| Pin 12 (RCK)           | Pico GPIO 8                              |
| Pin 13 (SRCK)          | Pico GPIO 9                              |
| Pins 14-17 (DRAIN 4-7) | LED cathodes via 160Ω resistors          |
| Pin 18 (SER OUT)       | Pin 3 (SER IN) of second TPIC            |

**Second TPIC (chain output)**
Same connections as first TPIC apart from the differences below:
- Pin 3 (SER IN) ← Pin 18 (SER OUT) of first TPIC
- Pin 18 (SER OUT) → not connected

### C3. LEDs Connections
- **LED anodes** → +5 V (common rail)
- **LED cathodes** → TPIC DRAIN outputs via 160 Ω resistor

### C4. Buttons Connections
- **Button 1** → One pin to GPIO 4 (Pico pin 6), other pin to GND
- **Button 2** → One pin to GPIO 5 (Pico pin 7), other pin to GND
- Internal pull-up resistors enabled in firmware (buttons active LOW)
---


## D. SOFTWARE
### D1. Firmware (MicroPython for Raspberry Pi Pico 2W RP2350)
- Download last version UF2 bootloader image from https://micropython.org/download/RPI_PICO2_W/
- Flash via USB mass storage mode

### D2. Program Structure
- `main.py`: main control program
- `index.html`: web interface for remote control and log viewing-exporting
- `microdot.py` : lightweight web server, download last version image from https://github.com/miguelgrinberg/microdot

### D3. Dependencies and References
- **Raspberry Pi Pico 2W:** https://www.raspberrypi.com/documentation/microcontrollers/
- **TPIC6B595N Datasheet:** https://www.ti.com/lit/ds/symlink/tpic6b595.pdf
- **MicroPython:** https://docs.micropython.org/en/latest/
- **Microdot:** https://microdot.readthedocs.io/en/latest/index.html#
---


## E. ENCLOSURE CONSIDERATIONS (to be printed according to provided 3D files)
**This is an open PCB design:**
- Description: PCB stand (2 possible tilt angles: 80° and 60°)
- The ML01 project deliberately does not include a fully enclosed protective case at this stage.
- This design choice allows all electronic components to remain visible, which is valuable for:  
        - Educational purposes and learning electronics<br>
        - Demonstrating the circuit layout and component placement<br>
        - Aesthetic appreciation of the assembled board

⚠️ **Safety Precautions while the device is powered:**
- **Do NOT touch** any part of the PCB except the two push buttons
- Risk of **electric shock** from exposed 5V circuitry
- Risk of **short circuits** causing component damage or failure
- Risk of **ESD damage** to sensitive components (Pico 2W, TPICs)

**This device is fragile:**
- Solder joints and component leads can break with rough handling
- Through-hole components are more robust than SMD but still require care
- Use the provided 3D-printed stand to minimize handling

**Indoor use only:**
- Indoor use in dry, controlled environments (typical household/office: 30–60% RH)
- Not rated for outdoor or humid environments (no conformal coating)
- Keep away from water, liquids, and excessive moisture
- Avoid dusty or dirty environments that could cause short circuits

**Recommended operating environment:**
- Recommended ambient: 15–30°C for optimal long-term reliability (mini 0°C to max 70°C)
- Keep away from direct sunlight to prevent overheating
- Workbench or desk in a clean (avoid directly on the ground)
- Display area with controlled access (away from children and pets)

❔**Future Enclosure Options:**
A protective enclosure may be offered in future revisions of this project if the need is actually confirmed.  
For now, users who require additional protection may design and 3D-print their own enclosure, ensuring adequate ventilation for heat dissipation.
---


## F. COMPLIANCE AND STANDARDS
This device is intended for personal, non-commercial use only.  
Users are responsible for ensuring compliance with local regulations if used in any commercial capacity.  
**It has not been tested or certified to meet:**
- CE electromagnetic compatibility standards
- FCC Part 15 regulations
- RoHS compliance (components should be RoHS-compliant when sourced)
---


*Revision date: 2026.01.10*<br>
© RELEASE255 | All rights reserved
