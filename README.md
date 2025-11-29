# ML01 PROJECT — DIY LED Board Powered by Raspberry Pico 2W
**Intelligent Open Hardware • Web-Controlled • THT Kit • Maker Friendly**

[![Hardware](https://img.shields.io/badge/Hardware-Open%20Source%20Intelligent-blueviolet?style=flat-square)](/hardware/)
[![Firmware](https://img.shields.io/badge/Firmware-Licence%20MIT-blue?style=flat-square)](/firmware/)
[![Docs&3d](https://img.shields.io/badge/Docs%20&%203d-Licence%20CC%20BY--NC--SA-orange?style=flat-square)](/docs)
[![Costs](https://img.shields.io/badge/Costs-Transparent-brightgreen?style=flat-square)](docs/cost_breakdown.pdf)
[![PCB](https://img.shields.io/badge/PCB-Proprietary-red?style=flat-square)](LICENSE.md)

![ML01 main photo](docs/images/product/main-photo.jpg)

<p align="center">
  <strong>Learn • Build • Control • Customize</strong><br>
  An open-source-intelligent lighting kit designed for makers who value freedom, quality, and transparency.
</p>

---

# 💡 Overview

**ML01** is a fully DIY through-hole LED board driven by a **Raspberry Pi Pico 2W** and two **TPIC6B595** shift registers.
It is both an educational tool and a customizable product, combining:

- Electronics learning
- Soldering practice
- Microcontroller programming
- Wireless control via Microdot
- Open hardware philosophy with protected PCB design

ML01 is built for **enthusiasts makers**, **learners**, and **creative tinkerers**.

---

# ✨ Key Features

- **LED Circle** — 16 yellow LEDs driven by 2× TPIC power shift registers
- **Physical Controls** — 2 buttons to switch operating modes
- **Wireless Web Interface** — Autonomous Microdot server for full remote control
- **ON Mode** — Turn all LEDs on
- **CHASE Mode** — Minute indicator synchronized via an NTP server
- **100% DIY THT** — Perfect for beginners and repair-friendly
- **Upgradable Firmware** — New modes and features can be added anytime
- **Flexible Power** — Works with the included 12.5 W PSU or via USB
- **Affordable** — You assemble it yourself, lowering production cost, Low Consumption ~1 Wh

<p align="center"><strong>ML01 = Learning + Creativity + Transparency</strong></p>

---

# 📦 Contents of the Kit

- PCB (THT)
- Raspberry Pi Pico 2W
- 12.5 W Raspberry power supply (5.1 V / 2.5 A)
- TPIC6B595 ICs
- LEDs
- Resistors
- Capacitors
- Resettable fuse
- Buttons
- Printed stand / support

---

# 🧠 Open-Source-Intelligent Philosophy

ML01 follows a **balanced open hardware model**:

### 🟢 100% OPEN
- Full firmware (MIT)
- Electronic schematics (PDF)
- Complete documentation
- BOM (Open license)
- Cost transparency
- No cookies, no trackers, no ads

### 🔒 PROTECTED
To preserve the value of the design, the following remain proprietary:
- KiCad source files
- PCB routing & layout
- Gerber files
- 3D model of the actual PCB

This ensures independence, sustainability, and creator protection.

---

# 📚 Documentation & How to Use

## 📸 Gallery

<p align="center">
  <img src="docs/images/product/front-view.jpg" width="45%">
  <img src="docs/images/product/back-view.jpg" width="45%">
</p>

<p align="center">
  <img src="docs/images/usage/web-interface.jpg" width="45%">
  <img src="docs/images/assembly/soldering.jpg" width="45%">
</p>

## 🚀 Quick Start

1. **Solder** all components following the guide
2. **Flash** the firmware to your Pico 2W
3. **Connect** to ML01 WiFi network
4. **Control** via web interface at http://ml01.local

⏱️ Assembly time: ~4 hours


## 1. Assembly  
📄 Follow the guide:
➡️ [Assembly Guide](docs/assembly_guide.pdf)

## 2. Flashing the Firmware  
- Copy the contents of `/firmware/` to your Pico 2W.
- Reboot.
- Connect to the ML01 Wi-Fi network.

## 3. Configuration  
Access the Web UI via Microdot: http://ml01.local or via the displayed IP.

## 4. Control  
Switch modes using the 2 physical buttons OR use the wireless web interface.

---

# ⚠️ Disclaimer

- This is a **DIY kit requiring soldering**.
- Assembly mistakes may damage components.
- No warranty is provided.
- Use at your own risk.

---

# �️ Where to Buy

- **Complete Kit:** [Available on Tindie](#) *(Coming soon)*
- **3D Printable Stand:** [Download on Printables](#) *(Coming soon)*

---

# 🗂️ Repository Structure

```
ML01/
├── README.md
├── LICENSE.md
├── CHANGELOG.md
│
├── docs/
│   ├── assembly_guide.pdf
│   ├── technical_specs.pdf
│   ├── cost_breakdown.pdf
│   └── images/
│       ├── product/
│       ├── assembly/
│       └── usage/
│
├── firmware/
│   ├── main.py
│   ├── index.html
│   ├── microdot.py
│   └── LICENSE
│
├── hardware/
│   ├── BOM.ods
│   ├── schematic.pdf
│   └── LICENSE
│
└── 3d/
    ├── board_stand.stl
    ├── board_stand.stp
    └── LICENSE
```

---

# 🤝 Contributions & Collaboration

Contributions to the **firmware** and **documentation** are welcome!

- Open issues for bugs, ideas, or improvements
- Submit pull requests for code or docs
- Proprietary files cannot be modified

### 🔍 Interested in partnering?
I'm open to collaborations with:

- Makers
- Hardware designers
- Open-source communities

Let's explore cross-promotion, joint tutorials, shared tools, or group orders.

---

# 🌐 Ecosystem

- 🛒 **Buy the kit:** *(Tindie link)*
- 🧱 **3D model:** *(Printables link)*
- 🌐 **Official website:** *(your-site.com)*
- 🐘 **Community:** *(Mastodon link)*
- 🔧 **Project page:** *(Hackaday.io link)*
- 💻 **Git repository:** *(GitHub link)*

---

# 📜 License Summary

ML01 uses a **multi-license** model:

| Area          | License         | File types         |
|---------------|-----------------|--------------------|
| Firmware      | MIT             | .py, .html         |
| Documentation | CC BY-NC-SA 4.0 | .pdf               |
| Schematics    | CC BY-NC-SA 4.0 | .pdf               |
| 3D Models     | CC BY-NC-SA 4.0 | .stl, .stp         |
| BOM           | CC BY-SA 4.0    | .ods               |
| Cost sheets   | Free use        | .pdf               |

**Proprietary:** KiCad source files, PCB layout, Gerbers.

<p align="center"><strong>ML01 — Open Source Hardware done responsibly.</strong></p>
