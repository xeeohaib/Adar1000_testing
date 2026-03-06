# ADAR1000 ↔ ZC702 FPGA SPI Interface

Verilog RTL that configures the **Analog Devices ADAR1000** 4-channel X/Ku-band
beamformer IC from a **Xilinx ZC702** (XC7Z020) FPGA board via the PMOD J63
connector and the ADAR1000-EVALZ P3 PMOD header.

The default configuration sequence (`RX1_MaxG_45`) sets RX Channel 1 to
**maximum gain** with a **45° phase shift** and is fully documented in
[`scripts/RX1_MaxG_45.txt`](scripts/RX1_MaxG_45.txt).

---

## Quick-Start

```
1. Wire ZC702 J63 → ADAR1000-EVALZ P3  (see docs/wiring_diagram.md)
2. Add rtl/*.v and constraints/zc702_pmod_j63.xdc to a Vivado RTL project
3. Synthesise → Implement → Generate Bitstream → Program Device
4. The ADAR1000 is auto-configured on FPGA startup; led_done_o lights when done
```

---

## Repository Layout

```
Adar1000_testing/
├── rtl/
│   ├── spi_master.v        SPI master (24-bit, Mode 0, MSB-first, CLK_DIV param)
│   ├── adar1000_ctrl.v     12-step register-write sequencer (RX1_MaxG_45)
│   └── top.v               Top-level wrapper; maps ports to PMOD J63 pins
├── sim/
│   ├── tb_spi_master.v     Unit testbench for spi_master
│   └── tb_adar1000_ctrl.v  Integration testbench for full config path
├── constraints/
│   └── zc702_pmod_j63.xdc  Vivado XDC: pin assignments + timing constraints
├── scripts/
│   └── RX1_MaxG_45.txt     Annotated SPI command script
└── docs/
    └── wiring_diagram.md   Step-by-step wiring guide, ASCII diagram, pin tables
```

---

## Hardware Connections (Summary)

| ZC702 J63 | FPGA Pin | Wire | ADAR1000-EVALZ P3 | Signal |
|-----------|----------|------|-------------------|--------|
| Pin 1 | AB14 | Yellow | Pin 4 | SCLK |
| Pin 2 | AA14 | Orange | Pin 2 | SDIO (MOSI) |
| Pin 3 | AA13 | Green  | Pin 3 | SDO (MISO) |
| Pin 4 | AB13 | Blue   | Pin 1 | CSB1 |
| Pin 5 | GND  | Black  | Pin 5 | GND |
| Pin 6 | 3.3 V | Red   | Pin 6 | VCC |

Full pinout, power-supply requirements, VNA verification steps, and
troubleshooting tips are in [`docs/wiring_diagram.md`](docs/wiring_diagram.md).

---

## Running Simulations

Requires [Icarus Verilog](http://iverilog.icarus.com/) (`iverilog` + `vvp`).

```bash
# SPI master unit test
cd sim
iverilog -o tb_spi_master  tb_spi_master.v  ../rtl/spi_master.v && vvp tb_spi_master

# Full configuration-path integration test
iverilog -o tb_adar1000_ctrl  tb_adar1000_ctrl.v \
         ../rtl/top.v ../rtl/adar1000_ctrl.v ../rtl/spi_master.v \
         && vvp tb_adar1000_ctrl
```

---

## SPI Protocol

| Parameter | Value |
|-----------|-------|
| Word width | 24 bits |
| Bit order | MSB first |
| Mode | SPI Mode 0 (CPOL=0, CPHA=0) |
| Default SCLK | 12.5 MHz (CLK_DIV=4, 100 MHz system clock) |
| Word format | `{0, 4'b0, addr[10:0], data[7:0]}` |

---

## RX1_MaxG_45 Configuration Sequence

| Step | SPI Word | Register | Data | Description |
|------|----------|----------|------|-------------|
| 1 | 0x000081 | 0x000 | 0x81 | Soft Reset |
| 2 | 0x000018 | 0x000 | 0x18 | Enable SDO, 4-wire SPI |
| 3 | 0x040055 | 0x400 | 0x55 | LDO trim ~1.8 V |
| 4 | 0x003860 | 0x038 | 0x60 | RAM Bypass |
| 5 | 0x002E7F | 0x02E | 0x7F | RX Enable (all 4 channels) |
| 6 | 0x003408 | 0x034 | 0x08 | LNA Bias |
| 7 | 0x003516 | 0x035 | 0x16 | RX VGA / VM Bias |
| 8 | 0x003120 | 0x031 | 0x20 | TR Switch to Receive mode |
| 9 | 0x0010FF | 0x010 | 0xFF | RX Ch1 Max Gain |
| 10 | 0x001436 | 0x014 | 0x36 | RX Ch1 I-value 45 degrees |
| 11 | 0x001536 | 0x015 | 0x36 | RX Ch1 Q-value 45 degrees |
| 12 | 0x002801 | 0x028 | 0x01 | LDRX Override (commit) |

---

## Implementation Methods

Three methods are available (see [`docs/wiring_diagram.md`](docs/wiring_diagram.md) for details):

| Method | This repo? | Description |
|--------|-----------|-------------|
| A — Pure PL Verilog | Yes | Self-contained FPGA logic, auto-runs at startup |
| B — Zynq PS SPI/EMIO | No | ARM CPU drives SPI via EMIO; Linux spidev |
| C — AXI Quad SPI IP | No | Vivado IP block, PS-controlled via AXI bus |

To request Method B or C, open an issue.
