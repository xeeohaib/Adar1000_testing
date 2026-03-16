// =============================================================================
// top.v
// -----------------------------------------------------------------------------
// Top-level integration: ADAR1000 SPI Configuration Core
//
// Targets : Xilinx ZC702 Evaluation Board (XC7Z020-CLG484-1)
// Clock   : 100 MHz supplied by Zynq PS FCLK0 (or external source)
// PMOD    : ZC702 connector J63 (12-pin) → ADAR1000-EVALZ P3 PMOD
//
// Connections (see constraints/zc702_pmod_j63.xdc for FPGA pin assignments):
//
//   FPGA port       J63 pin   Wire colour   ADAR1000-EVALZ P3 pin   Signal
//   ─────────────   ───────   ───────────   ─────────────────────   ──────
//   spi_sclk          1         Yellow          Pin 4               SCLK
//   spi_mosi          2         Orange          Pin 2               SDIO
//   spi_miso          3         Green           Pin 3               SDO
//   spi_csb           4         Blue            Pin 1               CSB1
//   GND               5         Black           Pin 5               GND
//   3.3 V             6         Red             Pin 6               VCC
//
// Operation:
//   After reset is de-asserted the controller waits for "go_i" (tied to '1'
//   via the XDC or driven by a push-button).  It then sequences through all
//   12 register writes that constitute the RX1_MaxG_45 configuration.
//   The on-board LED "led_done_o" lights when configuration is complete.
// =============================================================================
`timescale 1ns / 1ps

module top #(
    // SPI clock divider: SCLK = clk / (2 * SPI_CLK_DIV)
    // Default 4  → 12.5 MHz SPI clock from 100 MHz system clock
    parameter integer SPI_CLK_DIV = 4,

    // Post-reset wait cycles (100 µs @ 100 MHz)
    parameter integer RESET_WAIT_CYCLES = 10_000
)(
    // ── System ────────────────────────────────────────────────────────────────
    input  wire clk,          // 100 MHz system clock
    input  wire rst_n,        // Active-low reset (push button or PS)

    // ── Control ───────────────────────────────────────────────────────────────
    input  wire go_i,         // Tie high or connect to push-button to start
    output wire led_done_o,   // High when ADAR1000 configuration is complete

    // ── SPI / PMOD J63 ────────────────────────────────────────────────────────
    output wire spi_sclk,     // AB14 — J63 Pin 1 → ADAR1000 SCLK
    output wire spi_mosi,     // AA14 — J63 Pin 2 → ADAR1000 SDIO
    input  wire spi_miso,     // AA13 — J63 Pin 3 ← ADAR1000 SDO
    output wire spi_csb       // AB13 — J63 Pin 4 → ADAR1000 CSB1
);

    // ── Internal wires ────────────────────────────────────────────────────────
    wire        spi_start_w;
    wire [23:0] spi_tx_data_w;
    wire        spi_busy_w;
    wire        spi_done_w;
    wire        config_done_w;

    // ── SPI Master ────────────────────────────────────────────────────────────
    spi_master #(
        .CLK_DIV (SPI_CLK_DIV),
        .WIDTH   (24)
    ) u_spi_master (
        .clk      (clk),
        .rst_n    (rst_n),
        // Control
        .start    (spi_start_w),
        .tx_data  (spi_tx_data_w),
        .busy     (spi_busy_w),
        .done     (spi_done_w),
        .rx_data  (),           // unused for write-only sequence
        // SPI pins
        .sclk     (spi_sclk),
        .mosi     (spi_mosi),
        .miso     (spi_miso),
        .csb      (spi_csb)
    );

    // ── ADAR1000 Configuration Controller ────────────────────────────────────
    adar1000_ctrl #(
        .RESET_WAIT_CYCLES (RESET_WAIT_CYCLES)
    ) u_adar1000_ctrl (
        .clk         (clk),
        .rst_n       (rst_n),
        .go          (go_i),
        .config_done (config_done_w),
        // SPI master interface
        .spi_start   (spi_start_w),
        .spi_tx_data (spi_tx_data_w),
        .spi_busy    (spi_busy_w),
        .spi_done    (spi_done_w)
    );

    assign led_done_o = config_done_w;

endmodule
