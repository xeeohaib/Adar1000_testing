# =============================================================================
# zc702_pmod_j63.xdc
# -----------------------------------------------------------------------------
# Xilinx Design Constraints — ZC702 PMOD J63 → ADAR1000-EVALZ P3 PMOD
#
# Device : XC7Z020-CLG484-1 (ZC702 Evaluation Board)
# Bank   : 13  (VCCO = 3.3 V, LVCMOS33)
# Clock  : 100 MHz supplied via Zynq PS FCLK0 (see block-design clock wizard)
#
# ┌──────────────────────────────────────────────────────────────────────────┐
# │  FPGA port   │ J63 pin │ FPGA pin │  Wire  │ ADAR1000 P3 pin │  Signal  │
# ├──────────────────────────────────────────────────────────────────────────┤
# │  spi_sclk    │   1     │  AB14    │ Yellow │     Pin 4       │  SCLK    │
# │  spi_mosi    │   2     │  AA14    │ Orange │     Pin 2       │  SDIO    │
# │  spi_miso    │   3     │  AA13    │  Green │     Pin 3       │  SDO     │
# │  spi_csb     │   4     │  AB13    │  Blue  │     Pin 1       │  CSB1    │
# │  GND         │   5     │  GND     │  Black │     Pin 5       │  GND     │
# │  3.3 V       │   6     │  VCC     │   Red  │     Pin 6       │  VCC     │
# └──────────────────────────────────────────────────────────────────────────┘
#
# Note: The ADAR1000-EVALZ has on-board level translators (3.3 V ↔ 1.8 V).
#       No external level shifting is required on the ZC702 side.
#
# Note: Verify these pin numbers against the official Xilinx ZC702 schematic
#       (UG850) before tape-out.  Pin assignments are from the ZC702 board
#       files published by Xilinx/AMD (J63, Bank 13).
# =============================================================================

# ── Primary clock (100 MHz from PS FCLK0 via BUFG or clock wizard) ──────────
create_clock -period 10.000 -name clk [get_ports clk]

# ── SPI SCLK output (driven at ≤ 12.5 MHz; relax output timing) ─────────────
set_property -dict { PACKAGE_PIN AB14  IOSTANDARD LVCMOS33  SLEW SLOW  DRIVE 4 } \
             [get_ports spi_sclk]

# ── SPI MOSI / SDIO ──────────────────────────────────────────────────────────
set_property -dict { PACKAGE_PIN AA14  IOSTANDARD LVCMOS33  SLEW SLOW  DRIVE 4 } \
             [get_ports spi_mosi]

# ── SPI MISO / SDO ───────────────────────────────────────────────────────────
set_property -dict { PACKAGE_PIN AA13  IOSTANDARD LVCMOS33 } \
             [get_ports spi_miso]

# ── SPI CSB (Chip Select, active-low) ────────────────────────────────────────
set_property -dict { PACKAGE_PIN AB13  IOSTANDARD LVCMOS33  SLEW SLOW  DRIVE 4 } \
             [get_ports spi_csb]

# ── Configuration-complete LED (DS12 on ZC702 — MIO, or route to EMIO) ──────
# Uncomment and adjust if using a PL-connected LED.
# set_property -dict { PACKAGE_PIN Y21   IOSTANDARD LVCMOS33 } [get_ports led_done_o]

# ── Go push-button (SW7 on ZC702) ────────────────────────────────────────────
# Uncomment if go_i is connected to a push-button rather than a PS GPIO.
# set_property -dict { PACKAGE_PIN R27   IOSTANDARD LVCMOS25 } [get_ports go_i]

# ── Reset (active-low, SW4 on ZC702) ─────────────────────────────────────────
# set_property -dict { PACKAGE_PIN P16   IOSTANDARD LVCMOS25 } [get_ports rst_n]

# ── I/O timing constraints ────────────────────────────────────────────────────
# The ADAR1000 SPI setup/hold requirements at 12.5 MHz are easily met.
# Constrain outputs relative to the generated SCLK.
set_output_delay -clock clk  2.0  [get_ports spi_mosi]
set_output_delay -clock clk  2.0  [get_ports spi_csb]
set_output_delay -clock clk  2.0  [get_ports spi_sclk]
set_input_delay  -clock clk  2.0  [get_ports spi_miso]

# ── Bitstream configuration ───────────────────────────────────────────────────
set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4     [current_design]
set_property BITSTREAM.GENERAL.COMPRESS    TRUE  [current_design]
set_property CONFIG_VOLTAGE                3.3   [current_design]
set_property CFGBVS                        VCCO  [current_design]
