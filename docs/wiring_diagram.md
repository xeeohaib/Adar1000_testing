# ADAR1000-EVALZ ↔ ZC702 FPGA — Wiring Diagram & Step-by-Step Guide

## Overview

This document explains how to physically connect the **ADAR1000-EVALZ** phased-array beamformer board to the **Xilinx ZC702** evaluation board using the **PMOD J63** connector (ZC702) and the **P3 PMOD** header (ADAR1000-EVALZ), and then run the `RX1_MaxG_45` configuration that sets RX Channel 1 to maximum gain with a 45° phase shift.

---

## ⚠️ Implementation Method Selection

There are **three ways** to drive the ADAR1000 SPI from the ZC702.
This repository implements **Method A**. Methods B and C are described for reference.

| Method | Description | Pros | Cons |
|--------|-------------|------|------|
| **A — Pure PL Verilog (this repo)** | Custom SPI master in FPGA logic; starts automatically on power-up | No CPU required, deterministic timing, fully self-contained | Less flexible post-deployment |
| **B — Zynq PS SPI via EMIO** | ARM Cortex-A9 PS SPI controller routed through EMIO to PL I/O | Easy software control, Linux `spidev` driver available | Requires PS boot, slightly higher latency |
| **C — AXI Quad SPI IP Core** | Xilinx AXI Quad SPI IP in Vivado block design, driven by PS | Easy Vivado GUI integration, standard Xilinx driver | Requires AXI interconnect, PS configuration |

> **If you prefer Method B or C**, please open an issue or pull request and the implementation will be updated accordingly.

---

## Hardware Required

| Item | Quantity | Notes |
|------|----------|-------|
| Xilinx ZC702 Evaluation Board | 1 | XC7Z020-CLG484-1 |
| ADAR1000-EVALZ Evaluation Board | 1 | Analog Devices beamformer eval board |
| 6-pin PMOD-to-PMOD cable or jumper wires | 1 | Female-to-female, ≤ 150 mm recommended |
| External +3.3 V power supply | 1 | For ADAR1000 AVDD3 rail |
| External −5.0 V power supply | 1 | For ADAR1000 AVDD1 rail |
| USB-to-PC cable (micro-USB) | 1 | ZC702 JTAG/UART |
| Vivado Design Suite 2022.x or later | — | Free WebPACK edition is sufficient |

---

## Power Supply Requirements

The ADAR1000-EVALZ requires **two external power rails** in addition to the 3.3 V logic supply from the PMOD connector:

```
ADAR1000-EVALZ Power Connections
──────────────────────────────────────────────────────
  AVDD3 (J1 or terminal block)  →  +3.3 V  @ ≤ 500 mA
  AVDD1 (J1 or terminal block)  →  −5.0 V  @ ≤ 200 mA
  AGND                          →  Ground (common with ZC702 GND)
  Logic VCC (P3 Pin 6)          →  +3.3 V  (from ZC702 PMOD J63 Pin 6)
──────────────────────────────────────────────────────
```

> **⚠️ Warning:** The −5 V rail **cannot** be obtained from the ZC702 or the PMOD connector. A bench power supply or dedicated dc-dc converter is required.

---

## PMOD Connector Pinouts

### ZC702 PMOD J63 (12-pin)

```
    ZC702 J63 (top view, looking at the connector face)
    ┌────┬────┬────┬────┬─────┬──────┐
    │ P1 │ P2 │ P3 │ P4 │ GND │  VCC │   ← Row 1 (pins 1–6)
    ├────┼────┼────┼────┼─────┼──────┤
    │ P7 │ P8 │ P9 │P10 │ GND │  VCC │   ← Row 2 (pins 7–12)
    └────┴────┴────┴────┴─────┴──────┘

    Pin 1  : AB14  (spi_sclk)      Pin  7 : AB16  (spare)
    Pin 2  : AA14  (spi_mosi/SDIO) Pin  8 : Y15   (spare)
    Pin 3  : AA13  (spi_miso/SDO)  Pin  9 : AA15  (spare)
    Pin 4  : AB13  (spi_csb/CSB1)  Pin 10 : AB15  (spare)
    Pin 5  : GND                   Pin 11 : GND
    Pin 6  : VCC 3.3 V             Pin 12 : VCC 3.3 V
```

### ADAR1000-EVALZ P3 PMOD (6-pin, standard Digilent SPI Type-2)

```
    ADAR1000-EVALZ P3 (6-pin SPI PMOD header)
    ┌─────┬──────┬─────┬──────┬─────┬──────┐
    │ P1  │  P2  │  P3 │  P4  │ GND │  VCC │
    └─────┴──────┴─────┴──────┴─────┴──────┘

    Pin 1 : CSB1  (Chip Select, active-low)
    Pin 2 : SDIO  (SPI data in to ADAR1000, i.e. MOSI from FPGA)
    Pin 3 : SDO   (SPI data out from ADAR1000, i.e. MISO to FPGA)
    Pin 4 : SCLK  (SPI clock from FPGA)
    Pin 5 : GND
    Pin 6 : VCC   (3.3 V, powers the on-board level translators)
```

> **Note:** Verify the P3 pinout against the ADAR1000-EVALZ schematic in the
> Analog Devices evaluation board package before connecting.

---

## Wire-by-Wire Connection Table

| Wire # | Colour | ZC702 J63 | ZC702 FPGA Pin | ADAR1000-EVALZ P3 | Signal |
|--------|--------|-----------|----------------|-------------------|--------|
| 1 | 🟡 Yellow | Pin 1 | AB14 | Pin 4 | SCLK — SPI clock |
| 2 | 🟠 Orange | Pin 2 | AA14 | Pin 2 | SDIO — MOSI (FPGA→ADAR1000) |
| 3 | 🟢 Green | Pin 3 | AA13 | Pin 3 | SDO — MISO (ADAR1000→FPGA) |
| 4 | 🔵 Blue | Pin 4 | AB13 | Pin 1 | CSB1 — Chip Select |
| 5 | ⚫ Black | Pin 5 | GND | Pin 5 | Ground |
| 6 | 🔴 Red | Pin 6 | VCC (3.3 V) | Pin 6 | VCC — Logic supply |

---

## Step-by-Step Connection Procedure

### Step 1 — Inspect Both Boards

1. Power **OFF** both boards.
2. Locate **J63** on the ZC702 (12-pin PMOD, near the edge of the board between the XADC and FMC connectors; consult UG850 Figure 1-2).
3. Locate **P3** on the ADAR1000-EVALZ (6-pin SPI PMOD header; consult the ADAR1000-EVALZ schematic).

### Step 2 — Make Ground Connection First

Connect **J63 Pin 5 (GND) → P3 Pin 5 (GND)** with the black wire.
This establishes a common reference before any signal wires are attached.

### Step 3 — Connect the SPI Signals

Using the colour scheme from the table above:

```
  ZC702 J63 Pin 1 (AB14) ─── Yellow ──→ ADAR1000-EVALZ P3 Pin 4  [SCLK]
  ZC702 J63 Pin 2 (AA14) ─── Orange ──→ ADAR1000-EVALZ P3 Pin 2  [SDIO]
  ZC702 J63 Pin 3 (AA13) ─── Green  ←── ADAR1000-EVALZ P3 Pin 3  [SDO]
  ZC702 J63 Pin 4 (AB13) ─── Blue   ──→ ADAR1000-EVALZ P3 Pin 1  [CSB1]
```

### Step 4 — Connect Logic VCC

Connect **J63 Pin 6 (3.3 V) → P3 Pin 6 (VCC)** with the red wire.
This powers the ADAR1000-EVALZ SPI level translators.

### Step 5 — Connect External Power Supplies

**Before** powering on, connect the bench supplies to the ADAR1000-EVALZ:

```
  Bench supply +3.3 V ──→ AVDD3 terminal on ADAR1000-EVALZ
  Bench supply −5.0 V ──→ AVDD1 terminal on ADAR1000-EVALZ
  Bench supply GND    ──→ AGND  terminal on ADAR1000-EVALZ
  (use the same GND as ZC702)
```

Set current limits: **500 mA** for +3.3 V and **200 mA** for −5 V.

### Step 6 — Program the FPGA

1. Open **Vivado**, create a new RTL project and add all files under `rtl/`.
2. Add the constraints file `constraints/zc702_pmod_j63.xdc`.
3. In the top-level `top.v`, set parameters:
   - `SPI_CLK_DIV = 4` (SCLK = 12.5 MHz)
   - `RESET_WAIT_CYCLES = 10000` (100 µs)
4. Run **Synthesis → Implementation → Generate Bitstream**.
5. Open Hardware Manager, connect to the ZC702 via USB-JTAG, and program the device.

> **Tip — Zynq PS clock:** If you are using a Zynq block design, add a
> Clocking Wizard and configure FCLK0 = 100 MHz.  Connect FCLK0 to the
> `clk` port of `top`.  For a PL-only flow use the 200 MHz differential
> clock U64 and add an IBUFDS + MMCM/PLL to generate 100 MHz.

### Step 7 — Power-On Sequence

1. Power on the bench supplies (AVDD3, AVDD1) **first**.
2. Power on the ZC702 using its main 12 V supply.
3. Wait for the DONE LED on the ZC702 to illuminate (bitstream loaded).
4. The `go_i` input defaults to `1'b1` (see XDC) so configuration starts automatically.
5. `led_done_o` (mapped to a ZC702 LED) will illuminate when all 12 SPI writes have completed.

### Step 8 — Verify with VNA (Optional)

To reproduce the gain and return-loss measurements described in the problem statement:

1. Connect a **Vector Network Analyzer (VNA)** between the **RF_IO** SMA and the **RX1** SMA on the ADAR1000-EVALZ.
2. Sweep from **8 GHz to 16 GHz**.
3. **Expected results:**
   - Insertion gain (S21): **≈ +10 dB** at mid-band.
   - Return loss (S11 RX1 and S22 RF_IO): **< −10 dB** across most of the band.
   - Phase: **45°** shift applied to RX Channel 1.

---

## ASCII Wiring Diagram

```
   ZC702 FPGA (XC7Z020)                   ADAR1000-EVALZ
   ┌────────────────────┐                 ┌─────────────────────┐
   │                    │                 │                     │
   │  Bank 13 (3.3 V)   │                 │   P3 SPI PMOD       │
   │                    │                 │ ┌─────────────────┐ │
   │  AB14 ─────────────┼─── Yellow ──────┼─┤ Pin4  SCLK      │ │
   │  AA14 ─────────────┼─── Orange ──────┼─┤ Pin2  SDIO/MOSI │ │
   │  AA13 ─────────────┼─── Green  ──────┼─┤ Pin3  SDO/MISO  │ │
   │  AB13 ─────────────┼─── Blue   ──────┼─┤ Pin1  CSB1      │ │
   │  GND  ─────────────┼─── Black  ──────┼─┤ Pin5  GND       │ │
   │  3.3V ─────────────┼─── Red    ──────┼─┤ Pin6  VCC       │ │
   │                    │                 │ └─────────────────┘ │
   │   J63 PMOD         │                 │                     │
   └────────────────────┘                 │  AVDD3 ←── +3.3 V  │
                                          │  AVDD1 ←── −5.0 V  │
          USB-JTAG                        │  AGND  ──── GND     │
          │                               │                     │
   ┌──────┴───┐                           │  RF_IO ──── VNA P1  │
   │  Host PC │                           │  RX1   ──── VNA P2  │
   └──────────┘                           └─────────────────────┘
```

---

## SPI Protocol Details

| Parameter | Value |
|-----------|-------|
| Transaction width | 24 bits |
| Bit order | MSB first |
| SPI mode | Mode 0 (CPOL=0, CPHA=0) |
| Max SCLK | 50 MHz (ADAR1000 datasheet) |
| SCLK used here | 12.5 MHz (CLK_DIV=4, 100 MHz system clock) |
| CSB polarity | Active-low |
| Logic levels | 3.3 V (FPGA) ↔ 1.8 V (ADAR1000 core, via on-board translator) |

### 24-bit SPI Word Format

```
Bit  23     22…19       18…8         7…0
     ──────┬──────────┬────────────┬──────────
     R/W   │ Reserved │  Address   │  Data
     (0=W) │  (0000)  │  [10:0]    │  [7:0]
     ──────┴──────────┴────────────┴──────────

Example — Write 0x81 to register 0x000 (Soft Reset):
     0  0000  00000000000  10000001  = 0x000081

Example — Write 0x55 to register 0x400 (LDO trim):
     0  0000  10000000000  01010101  = 0x040055
```

---

## RX1_MaxG_45 Register Sequence

| Step | SPI Word | Address | Data | Description |
|------|----------|---------|------|-------------|
| 1 | `0x000081` | 0x000 | 0x81 | Soft Reset |
| 2 | `0x000018` | 0x000 | 0x18 | Enable SDO, 4-wire SPI |
| 3 | `0x040055` | 0x400 | 0x55 | Trim LDO to ≈1.8 V |
| 4 | `0x003860` | 0x038 | 0x60 | RAM Bypass — use working registers |
| 5 | `0x002E7F` | 0x02E | 0x7F | Receive Enable — all 4 channels |
| 6 | `0x003408` | 0x034 | 0x08 | LNA Bias |
| 7 | `0x003516` | 0x035 | 0x16 | RX VGA / Vector-Modulator bias |
| 8 | `0x003120` | 0x031 | 0x20 | TR Switch → Receive mode |
| 9 | `0x0010FF` | 0x010 | 0xFF | RX Ch1 gain = maximum (255) |
| 10 | `0x001436` | 0x014 | 0x36 | RX Ch1 Vector-Modulator I = 45° |
| 11 | `0x001536` | 0x015 | 0x36 | RX Ch1 Vector-Modulator Q = 45° |
| 12 | `0x002801` | 0x028 | 0x01 | LDRX Override — commit to RF path |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `led_done_o` never asserts | FPGA not programmed / `rst_n` stuck low | Check JTAG, re-program, confirm reset release |
| No SCLK on oscilloscope | Wrong J63 pin mapping | Verify AB14 vs board silk screen |
| SPI transactions visible but no RF response | AVDD1 (−5 V) not connected | Check bench supply polarity and connections |
| Gain lower than expected | LDO trim not applied (step 3 skipped) | Ensure `spi_done` between each write, check state machine |
| CSB stays low permanently | SPI master stuck in SHIFT state | Check for `spi_done` signal; increase CLK_DIV |
| VNA shows wrong phase | LDRX not executed (step 12) | Ensure all 12 transactions complete before measurement |

---

## Alternative: Using J62 Instead of J63

If J63 is occupied, use **J62**. The only change required is to update the XDC file:

| Signal | J62 FPGA Pin |
|--------|-------------|
| spi_sclk | Y12 |
| spi_mosi | W12 |
| spi_miso | V12 |
| spi_csb  | V13 |

Replace the four `set_property PACKAGE_PIN` lines in `constraints/zc702_pmod_j63.xdc` with the J62 pins above (keep all other settings identical).

---

## File Reference

```
Adar1000_testing/
├── rtl/
│   ├── spi_master.v        — 24-bit SPI master (Mode 0, MSB-first)
│   ├── adar1000_ctrl.v     — RX1_MaxG_45 register-write sequencer
│   └── top.v               — Top-level: ties controller + SPI master to PMOD
├── sim/
│   ├── tb_spi_master.v     — SPI master unit testbench
│   └── tb_adar1000_ctrl.v  — Full path integration testbench
├── constraints/
│   └── zc702_pmod_j63.xdc  — Vivado pin + timing constraints for J63
├── scripts/
│   └── RX1_MaxG_45.txt     — Annotated SPI command script
└── docs/
    └── wiring_diagram.md   — This document
```
