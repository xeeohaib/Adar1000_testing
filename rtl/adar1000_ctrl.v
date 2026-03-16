// =============================================================================
// adar1000_ctrl.v
// -----------------------------------------------------------------------------
// ADAR1000 Configuration Controller — RX1 Maximum Gain, 45° Phase Shift
//
// This module sequences 12 SPI register writes into the ADAR1000 to achieve
// the configuration documented in RX1_MaxG_45.txt.  On the rising edge of
// "go" the state machine begins and asserts "config_done" when finished.
//
// SPI word format (24 bits, MSB first):
//   [23]      : R/W  — 0 = write, 1 = read
//   [22:19]   : reserved, always 0
//   [18:8]    : 11-bit register address (A10 … A0)
//   [7:0]     : 8-bit register data
//
// Register sequence (RX1_MaxG_45.txt):
//   Step  1 — 0x000=0x81 : Soft Reset
//   Step  2 — 0x000=0x18 : Enable SDO, 4-wire SPI mode
//   Step  3 — 0x400=0x55 : Trim internal LDO to ≈1.8 V
//   Step  4 — 0x038=0x60 : RAM Bypass — use working registers
//   Step  5 — 0x02E=0x7F : Receive Enable — all 4 channels
//   Step  6 — 0x034=0x08 : LNA Bias
//   Step  7 — 0x035=0x16 : RX VGA / Vector-Modulator bias
//   Step  8 — 0x031=0x20 : TR Switch → Receive mode via SPI
//   Step  9 — 0x010=0xFF : RX Channel 1 gain = maximum (255)
//   Step 10 — 0x014=0x36 : RX Channel 1 Vector-Modulator I = 0x36 → 45°
//   Step 11 — 0x015=0x36 : RX Channel 1 Vector-Modulator Q = 0x36 → 45°
//   Step 12 — 0x028=0x01 : LDRX Override — commit settings to RF path
//
// Timing note: after the soft-reset write (step 1) a delay of at least
// RESET_WAIT_CYCLES system-clock cycles is inserted before step 2.
// Default: 10 000 cycles → 100 µs @ 100 MHz.
// =============================================================================
`timescale 1ns / 1ps

module adar1000_ctrl #(
    // Number of system-clock cycles to wait after soft-reset command
    parameter integer RESET_WAIT_CYCLES = 10_000
)(
    input  wire clk,          // System clock (100 MHz on ZC702)
    input  wire rst_n,        // Active-low synchronous reset
    input  wire go,           // Rising edge starts the configuration sequence

    output reg  config_done,  // Asserted (level) when all registers are written

    // ── SPI master interface ──────────────────────────────────────────────────
    output reg         spi_start,    // Pulse to begin one SPI transaction
    output reg  [23:0] spi_tx_data,  // 24-bit SPI word to send
    input  wire        spi_busy,     // High while SPI transaction is in progress
    input  wire        spi_done      // Single-cycle pulse when transaction ends
);

    // -------------------------------------------------------------------------
    // Configuration ROM  (12 entries × 24 bits)
    // -------------------------------------------------------------------------
    localparam integer NUM_REGS = 12;

    // Helper function — build 24-bit SPI write word from 11-bit address + 8-bit data
    // Format: {1'b0, 4'b0000, addr[10:0], data[7:0]}
    //   bit[23]   = 0           (write)
    //   bits[22:19] = 4'b0000  (reserved)
    //   bits[18:8]  = addr      (11-bit register address)
    //   bits[7:0]   = data      (8-bit register data)
    //
    // Cross-check against RX1_MaxG_45.txt notation (leading zeros dropped):
    //   addr=0x038, data=0x60 → 0x003860  ("3860")  ✓
    //   addr=0x400, data=0x55 → 0x040055  ("40055") ✓
    function automatic [23:0] spi_word;
        input [10:0] addr;
        input  [7:0] data;
        begin
            spi_word = {1'b0, 4'b0000, addr, data};
        end
    endfunction

    reg [23:0] cfg_rom [0:NUM_REGS-1];

    initial begin
        // Step 1 : Soft Reset
        cfg_rom[ 0] = spi_word(11'h000, 8'h81);
        // Step 2 : Enable SDO pin, select 4-wire SPI
        cfg_rom[ 1] = spi_word(11'h000, 8'h18);
        // Step 3 : Trim LDO to ~1.8 V
        cfg_rom[ 2] = spi_word(11'h400, 8'h55);
        // Step 4 : RAM Bypass — use working registers
        cfg_rom[ 3] = spi_word(11'h038, 8'h60);
        // Step 5 : Enable all four RX channels
        cfg_rom[ 4] = spi_word(11'h02E, 8'h7F);
        // Step 6 : Set LNA bias
        cfg_rom[ 5] = spi_word(11'h034, 8'h08);
        // Step 7 : Set RX VGA / Vector-Modulator bias
        cfg_rom[ 6] = spi_word(11'h035, 8'h16);
        // Step 8 : TR switch → Receive mode via SPI
        cfg_rom[ 7] = spi_word(11'h031, 8'h20);
        // Step 9 : RX Channel 1 gain = maximum (attenuator bypassed, VGA max)
        cfg_rom[ 8] = spi_word(11'h010, 8'hFF);
        // Step 10 : Channel 1 Vector-Modulator I-component → 45°
        cfg_rom[ 9] = spi_word(11'h014, 8'h36);
        // Step 11 : Channel 1 Vector-Modulator Q-component → 45°
        cfg_rom[10] = spi_word(11'h015, 8'h36);
        // Step 12 : LDRX Override — push settings into active RF path
        cfg_rom[11] = spi_word(11'h028, 8'h01);
    end

    // -------------------------------------------------------------------------
    // Wait-counter width
    // -------------------------------------------------------------------------
    localparam integer WAIT_W = $clog2(RESET_WAIT_CYCLES + 1);

    // ── State encoding ────────────────────────────────────────────────────────
    localparam [2:0]
        S_IDLE       = 3'd0,   // Waiting for go
        S_LAUNCH     = 3'd1,   // Issue spi_start for current step
        S_WAIT_SPI   = 3'd2,   // Wait for SPI master to finish
        S_RST_DELAY  = 3'd3,   // Post-soft-reset delay
        S_ADVANCE    = 3'd4,   // Move to next step
        S_DONE       = 3'd5;   // All registers written

    // ── Registers ─────────────────────────────────────────────────────────────
    reg [2:0]          state;
    reg [3:0]          step;          // Current ROM index (0..NUM_REGS-1)
    reg [WAIT_W-1:0]   wait_cnt;
    reg                go_prev;       // For rising-edge detect on go

    // ── State machine ─────────────────────────────────────────────────────────
    always @(posedge clk) begin
        if (!rst_n) begin
            state       <= S_IDLE;
            step        <= 4'd0;
            wait_cnt    <= {WAIT_W{1'b0}};
            config_done <= 1'b0;
            spi_start   <= 1'b0;
            spi_tx_data <= 24'd0;
            go_prev     <= 1'b0;
        end else begin
            spi_start <= 1'b0;   // default: no start pulse
            go_prev   <= go;

            case (state)
                // --------------------------------------------------------------
                S_IDLE: begin
                    config_done <= 1'b0;
                    step        <= 4'd0;
                    if (go && !go_prev) begin   // rising edge of go
                        state <= S_LAUNCH;
                    end
                end

                // --------------------------------------------------------------
                // Load ROM word and issue a single-cycle start pulse
                // --------------------------------------------------------------
                S_LAUNCH: begin
                    spi_tx_data <= cfg_rom[step];
                    spi_start   <= 1'b1;
                    state       <= S_WAIT_SPI;
                end

                // --------------------------------------------------------------
                // Wait until the SPI master signals completion
                // --------------------------------------------------------------
                S_WAIT_SPI: begin
                    if (spi_done) begin
                        // After step 0 (soft-reset) insert a mandatory delay
                        if (step == 4'd0) begin
                            wait_cnt <= {WAIT_W{1'b0}};
                            state    <= S_RST_DELAY;
                        end else begin
                            state <= S_ADVANCE;
                        end
                    end
                end

                // --------------------------------------------------------------
                // Mandatory post-reset delay (≥ 100 µs @ 100 MHz)
                // --------------------------------------------------------------
                S_RST_DELAY: begin
                    if (wait_cnt == WAIT_W'(RESET_WAIT_CYCLES - 1)) begin
                        state <= S_ADVANCE;
                    end else begin
                        wait_cnt <= wait_cnt + 1'b1;
                    end
                end

                // --------------------------------------------------------------
                // Advance to next ROM entry or finish
                // --------------------------------------------------------------
                S_ADVANCE: begin
                    if (step == NUM_REGS - 1) begin
                        state <= S_DONE;
                    end else begin
                        step  <= step + 1'b1;
                        state <= S_LAUNCH;
                    end
                end

                // --------------------------------------------------------------
                S_DONE: begin
                    config_done <= 1'b1;
                    // Remain in DONE until reset or a new go pulse
                    if (go && !go_prev) begin
                        config_done <= 1'b0;
                        step        <= 4'd0;
                        state       <= S_LAUNCH;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
