// =============================================================================
// spi_master.v
// -----------------------------------------------------------------------------
// 24-bit SPI Master for ADAR1000 Beamformer
//
// Protocol : SPI Mode 0 (CPOL=0, CPHA=0)
//            Data sampled on rising SCLK edge, shifted on falling SCLK edge.
//            MSB transmitted first.  24-bit transaction width.
//
// Clock    : System clock divided by (2 * CLK_DIV) produces the SPI clock.
//            Default CLK_DIV=4 with a 100 MHz system clock → SCLK = 12.5 MHz,
//            well within the ADAR1000 50 MHz maximum.
//
// Timing   : CSB asserted (low) → idle half-period → 24 SCLK cycles →
//            hold half-period → CSB deasserted (high) → done pulse
//
// ZC702 Connection (PMOD J63 → ADAR1000-EVALZ P3 PMOD):
//   sclk  → J63 Pin 1 (AB14) → P3 Pin 4 (SCLK)
//   mosi  → J63 Pin 2 (AA14) → P3 Pin 2 (SDIO)
//   miso  → J63 Pin 3 (AA13) → P3 Pin 3 (SDO)
//   csb   → J63 Pin 4 (AB13) → P3 Pin 1 (CSB1)
//   GND   → J63 Pin 5        → P3 Pin 5 (GND)
//   3.3 V → J63 Pin 6        → P3 Pin 6 (VCC)
//
// 24-bit SPI word format (ADAR1000):
//   bit[23]    : R/W  (0 = write)
//   bits[22:19]: reserved (0000)
//   bits[18:8] : 11-bit register address
//   bits[7:0]  : 8-bit data
// =============================================================================
`timescale 1ns / 1ps

module spi_master #(
    // SCLK frequency = clk / (2 * CLK_DIV).  Minimum value: 2.
    parameter integer CLK_DIV = 4,
    // SPI transaction width in bits.
    parameter integer WIDTH   = 24
)(
    input  wire              clk,       // System clock (100 MHz on ZC702)
    input  wire              rst_n,     // Active-low synchronous reset

    // ── Control interface ─────────────────────────────────────────────────────
    input  wire              start,     // Pulse high for 1 cycle to start transfer
    input  wire [WIDTH-1:0]  tx_data,   // Data to send, MSB first
    output reg               busy,      // High during a transaction
    output reg               done,      // Single-cycle pulse when transaction ends
    output reg  [WIDTH-1:0]  rx_data,   // Data received from slave (SDO)

    // ── SPI pins ──────────────────────────────────────────────────────────────
    output reg               sclk,      // SPI clock
    output wire              mosi,      // Master Out Slave In (SDIO on ADAR1000)
    input  wire              miso,      // Master In Slave Out (SDO on ADAR1000)
    output reg               csb        // Chip Select Bar, active-low
);

    // -------------------------------------------------------------------------
    // Local-parameter widths — avoid zero-width signals for small parameters
    // -------------------------------------------------------------------------
    localparam DIV_W = (CLK_DIV <= 1)   ? 1 : $clog2(CLK_DIV);
    localparam BIT_W = $clog2(WIDTH);   // e.g. 5 for WIDTH=24

    // ── State encoding ────────────────────────────────────────────────────────
    localparam [2:0]
        S_IDLE   = 3'd0,   // Wait for start pulse
        S_ASSERT = 3'd1,   // Assert CSB, wait one half-period
        S_SHIFT  = 3'd2,   // Shift 24 bits
        S_HOLD   = 3'd3,   // Hold one half-period after last SCLK falling edge
        S_DONE   = 3'd4;   // Deassert CSB, pulse done

    // ── Registers ─────────────────────────────────────────────────────────────
    reg [2:0]         state;
    reg [DIV_W-1:0]   clk_cnt;     // Clock-divider counter
    reg [BIT_W-1:0]   bit_cnt;     // Remaining bits (counts down from WIDTH-1)
    reg [WIDTH-1:0]   tx_shift;    // TX shift register
    reg [WIDTH-1:0]   rx_shift;    // RX shift register

    // MOSI is driven combinatorially from the MSB of the TX shift register
    assign mosi = tx_shift[WIDTH-1];

    // ── Main state machine ────────────────────────────────────────────────────
    always @(posedge clk) begin
        if (!rst_n) begin
            state    <= S_IDLE;
            busy     <= 1'b0;
            done     <= 1'b0;
            sclk     <= 1'b0;
            csb      <= 1'b1;
            tx_shift <= {WIDTH{1'b0}};
            rx_shift <= {WIDTH{1'b0}};
            rx_data  <= {WIDTH{1'b0}};
            clk_cnt  <= {DIV_W{1'b0}};
            bit_cnt  <= {BIT_W{1'b0}};
        end else begin
            done <= 1'b0; // default: done is a single-cycle pulse

            case (state)
                // ----------------------------------------------------------
                S_IDLE: begin
                    sclk <= 1'b0;
                    csb  <= 1'b1;
                    busy <= 1'b0;
                    if (start) begin
                        tx_shift <= tx_data;
                        bit_cnt  <= WIDTH[BIT_W-1:0] - 1'b1;
                        clk_cnt  <= {DIV_W{1'b0}};
                        busy     <= 1'b1;
                        state    <= S_ASSERT;
                    end
                end

                // ----------------------------------------------------------
                // Assert CSB and wait one half-period before the first SCLK edge
                // ----------------------------------------------------------
                S_ASSERT: begin
                    csb <= 1'b0;
                    if (clk_cnt == DIV_W'(CLK_DIV - 1)) begin
                        clk_cnt <= {DIV_W{1'b0}};
                        state   <= S_SHIFT;
                    end else begin
                        clk_cnt <= clk_cnt + 1'b1;
                    end
                end

                // ----------------------------------------------------------
                // Shift 24 bits — toggle SCLK every CLK_DIV system cycles
                // ----------------------------------------------------------
                S_SHIFT: begin
                    if (clk_cnt == DIV_W'(CLK_DIV - 1)) begin
                        clk_cnt <= {DIV_W{1'b0}};
                        sclk    <= ~sclk;

                        if (!sclk) begin
                            // ── Rising edge: sample MISO (MSB first into LSB) ──
                            rx_shift <= {rx_shift[WIDTH-2:0], miso};
                        end else begin
                            // ── Falling edge: advance TX shift register ────────
                            if (bit_cnt == {BIT_W{1'b0}}) begin
                                // All bits clocked — wait hold period
                                state <= S_HOLD;
                            end else begin
                                tx_shift <= {tx_shift[WIDTH-2:0], 1'b0};
                                bit_cnt  <= bit_cnt - 1'b1;
                            end
                        end
                    end else begin
                        clk_cnt <= clk_cnt + 1'b1;
                    end
                end

                // ----------------------------------------------------------
                // Hold CSB low for one half-period after the last SCLK edge
                // ----------------------------------------------------------
                S_HOLD: begin
                    if (clk_cnt == DIV_W'(CLK_DIV - 1)) begin
                        clk_cnt <= {DIV_W{1'b0}};
                        state   <= S_DONE;
                    end else begin
                        clk_cnt <= clk_cnt + 1'b1;
                    end
                end

                // ----------------------------------------------------------
                S_DONE: begin
                    csb     <= 1'b1;
                    rx_data <= {rx_shift[WIDTH-2:0], miso}; // capture last bit
                    done    <= 1'b1;
                    busy    <= 1'b0;
                    state   <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
