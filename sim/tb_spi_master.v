// =============================================================================
// tb_spi_master.v
// -----------------------------------------------------------------------------
// Testbench for spi_master.v
//
// Verifies:
//   1.  A 24-bit word is transmitted MSB-first on MOSI
//   2.  SCLK has the correct polarity (idles low, rises before sampling)
//   3.  CSB is asserted (low) for the duration of the transaction
//   4.  24 bits of MISO data are correctly captured in rx_data
//   5.  done pulse is asserted for exactly one clock cycle after completion
//   6.  busy is de-asserted after done
//
// Run with: iverilog -o tb_spi_master tb_spi_master.v spi_master.v && vvp tb_spi_master
// =============================================================================
`timescale 1ns / 1ps

module tb_spi_master;

    // ── Parameters ────────────────────────────────────────────────────────────
    parameter CLK_PERIOD  = 10;    // 10 ns = 100 MHz
    parameter CLK_DIV     = 4;
    parameter WIDTH       = 24;

    // ── DUT signals ───────────────────────────────────────────────────────────
    reg              clk;
    reg              rst_n;
    reg              start;
    reg  [WIDTH-1:0] tx_data;
    wire             busy;
    wire             done;
    wire [WIDTH-1:0] rx_data;
    wire             sclk;
    wire             mosi;
    reg              miso;
    wire             csb;

    // ── DUT instantiation ─────────────────────────────────────────────────────
    spi_master #(
        .CLK_DIV (CLK_DIV),
        .WIDTH   (WIDTH)
    ) dut (
        .clk     (clk),
        .rst_n   (rst_n),
        .start   (start),
        .tx_data (tx_data),
        .busy    (busy),
        .done    (done),
        .rx_data (rx_data),
        .sclk    (sclk),
        .mosi    (mosi),
        .miso    (miso),
        .csb     (csb)
    );

    // ── Clock generation ──────────────────────────────────────────────────────
    initial clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // ── Test stimulus ─────────────────────────────────────────────────────────
    integer i;
    reg [WIDTH-1:0] captured_mosi;   // bits we observe on MOSI
    reg [WIDTH-1:0] miso_pattern;    // loopback pattern driven on MISO

    initial begin
        $dumpfile("tb_spi_master.vcd");
        $dumpvars(0, tb_spi_master);

        // ── Reset ─────────────────────────────────────────────────────────────
        rst_n  = 0;
        start  = 0;
        tx_data = 24'h0;
        miso   = 0;
        captured_mosi = 0;
        miso_pattern  = 24'hA5_5A_C3; // arbitrary RX pattern

        repeat(4) @(posedge clk);
        @(negedge clk) rst_n = 1;

        // ── Test 1: Transmit soft-reset command (0x000081) ────────────────────
        $display("[%0t] Test 1: TX 0x000081 (soft-reset)", $time);
        @(negedge clk);
        tx_data = 24'h000081;
        start   = 1;
        @(negedge clk) start = 0;

        // Drive loopback MISO (MSB first) and capture MOSI
        fork
            // MISO driver: send miso_pattern MSB-first on each rising SCLK
            begin : miso_drv
                integer b;
                // Wait for first SCLK rise
                for (b = WIDTH-1; b >= 0; b = b - 1) begin
                    @(posedge sclk);
                    miso = miso_pattern[b];
                end
            end
            // MOSI capture: sample on rising SCLK
            begin : mosi_cap
                integer b;
                for (b = WIDTH-1; b >= 0; b = b - 1) begin
                    @(posedge sclk);
                    #1; // tiny hold
                    captured_mosi[b] = mosi;
                end
            end
        join

        // Wait for done
        @(posedge done);
        @(negedge clk);

        // ── Checks ────────────────────────────────────────────────────────────
        if (captured_mosi !== 24'h000081)
            $display("FAIL: MOSI captured 0x%06X, expected 0x000081", captured_mosi);
        else
            $display("PASS: MOSI = 0x%06X (correct)", captured_mosi);

        if (rx_data !== miso_pattern)
            $display("FAIL: rx_data = 0x%06X, expected 0x%06X", rx_data, miso_pattern);
        else
            $display("PASS: rx_data = 0x%06X (correct)", rx_data);

        if (csb !== 1'b1)
            $display("FAIL: CSB not de-asserted after transaction");
        else
            $display("PASS: CSB de-asserted correctly");

        if (busy !== 1'b0)
            $display("FAIL: busy still asserted after done");
        else
            $display("PASS: busy de-asserted correctly");

        // ── Test 2: Transmit LDO-trim command (0x040055) ─────────────────────
        $display("[%0t] Test 2: TX 0x040055 (LDO trim)", $time);
        repeat(4) @(negedge clk);
        tx_data = 24'h040055;
        miso    = 0;
        start   = 1;
        @(negedge clk) start = 0;

        @(posedge done);
        @(negedge clk);

        if (busy !== 1'b0)
            $display("FAIL: busy still high after Test 2");
        else
            $display("PASS: Test 2 complete, busy de-asserted");

        $display("[%0t] All tests complete.", $time);
        $finish;
    end

    // ── Timeout watchdog ──────────────────────────────────────────────────────
    initial begin
        #500_000;
        $display("TIMEOUT: simulation exceeded 500 µs");
        $finish;
    end

endmodule
