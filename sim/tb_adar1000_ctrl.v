// =============================================================================
// tb_adar1000_ctrl.v
// -----------------------------------------------------------------------------
// Testbench for the complete ADAR1000 configuration path:
//   top → adar1000_ctrl → spi_master
//
// A simplified ADAR1000 SPI slave model captures each 24-bit write and checks
// it against the expected RX1_MaxG_45 sequence.
//
// Run with:
//   iverilog -o tb_adar1000_ctrl tb_adar1000_ctrl.v \
//            ../rtl/top.v ../rtl/adar1000_ctrl.v ../rtl/spi_master.v \
//            && vvp tb_adar1000_ctrl
// =============================================================================
`timescale 1ns / 1ps

module tb_adar1000_ctrl;

    // ── DUT wires ─────────────────────────────────────────────────────────────
    reg  clk;
    reg  rst_n;
    reg  go;
    wire led_done;
    wire sclk;
    wire mosi;
    reg  miso;
    wire csb;

    // ── DUT — instantiate the full top-level ──────────────────────────────────
    // Use a short reset delay so simulation runs fast
    top #(
        .SPI_CLK_DIV       (4),
        .RESET_WAIT_CYCLES (20)    // shorten for simulation
    ) dut (
        .clk       (clk),
        .rst_n     (rst_n),
        .go_i      (go),
        .led_done_o(led_done),
        .spi_sclk  (sclk),
        .spi_mosi  (mosi),
        .spi_miso  (miso),
        .spi_csb   (csb)
    );

    // ── Clock ─────────────────────────────────────────────────────────────────
    initial clk = 0;
    always #5 clk = ~clk;           // 100 MHz

    // ── ADAR1000 SPI slave model ──────────────────────────────────────────────
    // Capture every 24-bit write transaction and verify it matches expected ROM.
    reg  [23:0] rx_word;
    integer     trans_count;    // Transaction counter

    // Expected RX1_MaxG_45 sequence (24-bit SPI words)
    // Format: {1'b0, 4'b0, addr[10:0], data[7:0]}
    reg [23:0] expected [0:11];
    initial begin
        expected[ 0] = 24'h000081;   // Soft Reset
        expected[ 1] = 24'h000018;   // Enable SDO, 4-wire SPI
        expected[ 2] = 24'h040055;   // LDO trim
        expected[ 3] = 24'h003860;   // RAM Bypass
        expected[ 4] = 24'h002E7F;   // RX Enable (all channels)
        expected[ 5] = 24'h003408;   // LNA Bias
        expected[ 6] = 24'h003516;   // RX Bias
        expected[ 7] = 24'h003120;   // TR Switch → RX
        expected[ 8] = 24'h0010FF;   // RX Ch1 Max Gain
        expected[ 9] = 24'h001436;   // RX Ch1 I = 0x36 (45°)
        expected[10] = 24'h001536;   // RX Ch1 Q = 0x36 (45°)
        expected[11] = 24'h002801;   // LDRX Override
    end

    // Slave receive task: clocks in 24 bits on rising SCLK edges while CSB=0
    task automatic slave_receive;
        output [23:0] word;
        integer b;
        begin
            word = 24'd0;
            // Wait for CSB assertion — if CSB is already low when we arrive,
            // wait for it to go high first so we always start on a clean negedge.
            if (!csb) @(posedge csb);
            @(negedge csb);          // wait for CS asserted
            for (b = 23; b >= 0; b = b - 1) begin
                @(posedge sclk);
                #1;
                word[b] = mosi;
            end
            @(posedge csb);          // wait for CS released
        end
    endtask

    // Slave process — starts before reset so it never misses the first transaction
    initial begin
        trans_count = 0;
        miso = 0;
        // Start listening immediately (before rst_n or go); slave_receive
        // will block on @(negedge csb) so no transaction is missed.
        forever begin
            slave_receive(rx_word);
            if (trans_count < 12) begin
                if (rx_word !== expected[trans_count]) begin
                    $display("FAIL [trans %0d]: got 0x%06X, expected 0x%06X",
                             trans_count, rx_word, expected[trans_count]);
                end else begin
                    $display("PASS [trans %0d]: 0x%06X", trans_count, rx_word);
                end
            end
            trans_count = trans_count + 1;
        end
    end

    // ── Stimulus ──────────────────────────────────────────────────────────────
    initial begin
        $dumpfile("tb_adar1000_ctrl.vcd");
        $dumpvars(0, tb_adar1000_ctrl);

        rst_n = 0;
        go    = 0;
        repeat(8) @(posedge clk);
        @(negedge clk) rst_n = 1;
        repeat(4) @(posedge clk);

        // Assert go for one cycle to start configuration
        @(negedge clk) go = 1;
        @(negedge clk) go = 0;

        // Wait for configuration-complete flag
        @(posedge led_done);
        @(negedge clk);

        if (trans_count == 12)
            $display("PASS: All 12 SPI transactions completed.");
        else
            $display("FAIL: Expected 12 transactions, got %0d", trans_count);

        $display("[%0t] Simulation complete. led_done = %b", $time, led_done);
        #200 $finish;
    end

    // ── Timeout watchdog ──────────────────────────────────────────────────────
    initial begin
        #5_000_000;   // 5 ms simulation limit
        $display("TIMEOUT: simulation exceeded 5 ms");
        $finish;
    end

endmodule
