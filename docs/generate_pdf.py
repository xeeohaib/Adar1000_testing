#!/usr/bin/env python3
"""
generate_pdf.py
Generates docs/ADAR1000_ZC702_Setup_Guide.pdf using ReportLab.
All diagrams are drawn programmatically as vector graphics inside the PDF.
"""

import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import (
    Drawing, Rect, Line, String, Polygon, Circle, PolyLine, Path
)
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import colors as rcolors

# ── colour palette ────────────────────────────────────────────────────────────
BG_DARK   = colors.HexColor("#1a1a2e")
BG_PANEL  = colors.HexColor("#0d2137")
BG_BOARD  = colors.HexColor("#0b3d6e")
ACCENT    = colors.HexColor("#5bc0eb")
ACCENT2   = colors.HexColor("#a0c4ff")
TEXT_MAIN = colors.HexColor("#e0e0e0")
TEXT_DIM  = colors.HexColor("#7090a0")
YELLOW    = colors.HexColor("#fdd835")
ORANGE    = colors.HexColor("#ff9800")
GREEN     = colors.HexColor("#4caf50")
BLUE      = colors.HexColor("#64b5f6")
RED       = colors.HexColor("#ef5350")
GREY      = colors.HexColor("#90a4ae")
PURPLE    = colors.HexColor("#ce93d8")
TEAL      = colors.HexColor("#4dd0e1")
PINK      = colors.HexColor("#ff5aad")
CYAN_BG   = colors.HexColor("#0a1e30")
RED_BOARD = colors.HexColor("#a53030")
RED_DARK  = colors.HexColor("#2a0808")
GOLD      = colors.HexColor("#ffd54f")

OUT_PATH = os.path.join(os.path.dirname(__file__), "ADAR1000_ZC702_Setup_Guide.pdf")


# ─────────────────────────────────────────────────────────────────────────────
# Custom flowables
# ─────────────────────────────────────────────────────────────────────────────

class WiringDiagram(Flowable):
    """Vector wiring diagram drawn with ReportLab shapes."""
    W, H = 480, 220

    def wrap(self, *args):
        return self.W, self.H

    def draw(self):
        c = self.canv
        # ── ZC702 board ──────────────────────────────────────────────────────
        c.setFillColor(colors.HexColor("#0d2137"))
        c.setStrokeColor(colors.HexColor("#1e6ab5"))
        c.setLineWidth(1.5)
        c.roundRect(5, 10, 180, 200, 6, fill=1, stroke=1)

        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(95, 198, "ZC702 (XC7Z020)")
        c.setFont("Helvetica", 7)
        c.setFillColor(ACCENT2)
        c.drawCentredString(95, 188, "Bank 13 · LVCMOS33 · 3.3 V")

        # Zynq chip inside ZC702
        c.setFillColor(colors.HexColor("#0b3d6e"))
        c.setStrokeColor(colors.HexColor("#3a86c8"))
        c.setLineWidth(1)
        c.roundRect(15, 130, 160, 50, 4, fill=1, stroke=1)
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(95, 168, "Zynq XC7Z020")
        c.setFillColor(ACCENT2)
        c.setFont("Helvetica", 6)
        c.drawCentredString(95, 158, "spi_master.v  +  adar1000_ctrl.v")
        c.drawCentredString(95, 149, "100 MHz PL Fabric")

        # J63 connector block
        c.setFillColor(colors.HexColor("#0b2a40"))
        c.setStrokeColor(colors.HexColor("#2a6faa"))
        c.roundRect(15, 50, 160, 70, 4, fill=1, stroke=1)
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(95, 108, "PMOD J63")

        # 6 pin circles on J63
        pin_colors = [YELLOW, ORANGE, GREEN, BLUE, GREY, RED]
        pin_labels = ["1\nAB14\nSCLK", "2\nAA14\nMOSI", "3\nAA13\nMISO",
                      "4\nAB13\nCSB", "5\nGND", "6\n3.3V"]
        for i, (col, lbl) in enumerate(zip(pin_colors, pin_labels)):
            x = 28 + i * 26
            y = 78
            c.setFillColor(col)
            c.setStrokeColor(colors.white)
            c.setLineWidth(0.5)
            c.circle(x, y, 9, fill=1, stroke=1)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 5)
            lines = lbl.split("\n")
            for j, l in enumerate(lines):
                c.drawCentredString(x, y + 4 - j * 6, l)

        # ── Wires (centre) ───────────────────────────────────────────────────
        wire_data = [
            (YELLOW, 56,  78, 295, 115, "SCLK"),
            (ORANGE, 82,  78, 295,  98, "SDIO/MOSI"),
            (GREEN,  108, 78, 295,  81, "SDO/MISO"),
            (BLUE,   134, 78, 295,  64, "CSB1"),
            (GREY,   160, 78, 295,  47, "GND"),
            (RED,    186, 78, 295,  30, "VCC"),
        ]
        for col, x1, y1, x2, y2, lbl in wire_data:
            c.setStrokeColor(col)
            c.setLineWidth(2)
            # dashed for the crossing region
            c.setDash(6, 3)
            c.line(x1 + 10, y1, x2 - 10, y2)
            c.setDash()
            c.line(x1, y1, x1 + 10, y1)
            c.line(x2 - 10, y2, x2, y2)
            c.setFillColor(col)
            c.setFont("Helvetica", 5.5)
            c.drawCentredString((x1 + x2) // 2, (y1 + y2) // 2 + 3, lbl)

        # ── ADAR1000-EVALZ board ─────────────────────────────────────────────
        c.setFillColor(RED_DARK)
        c.setStrokeColor(RED_BOARD)
        c.setLineWidth(1.5)
        c.roundRect(295, 10, 180, 200, 6, fill=1, stroke=1)

        c.setFillColor(colors.HexColor("#ff6b6b"))
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(385, 198, "ADAR1000-EVALZ")
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor("#cc8080"))
        c.drawCentredString(385, 188, "4-Ch Beamformer · 8–16 GHz")

        # ADAR1000 chip
        c.setFillColor(colors.HexColor("#3a0c0c"))
        c.setStrokeColor(colors.HexColor("#993333"))
        c.roundRect(305, 130, 160, 50, 4, fill=1, stroke=1)
        c.setFillColor(colors.HexColor("#ff6b6b"))
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(385, 168, "ADAR1000 IC")
        c.setFont("Helvetica", 6)
        c.setFillColor(colors.HexColor("#cc8080"))
        c.drawCentredString(385, 158, "LNA + VGA + Vector Modulator × 4")
        c.drawCentredString(385, 149, "SPI Registers + Beam RAM")

        # Level translators
        c.setFillColor(colors.HexColor("#1a1a00"))
        c.setStrokeColor(colors.HexColor("#c8a000"))
        c.roundRect(305, 100, 160, 26, 4, fill=1, stroke=1)
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(385, 114, "Level Translators  3.3 V ↔ 1.8 V")

        # P3 header connector
        c.setFillColor(colors.HexColor("#200808"))
        c.setStrokeColor(colors.HexColor("#993333"))
        c.roundRect(305, 20, 160, 72, 4, fill=1, stroke=1)
        c.setFillColor(colors.HexColor("#ff6b6b"))
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(385, 82, "P3 PMOD Header")

        p3_pin_labels = ["CSB1", "SDIO", "SDO", "SCLK", "GND", "VCC"]
        p3_pin_colors = [BLUE, ORANGE, GREEN, YELLOW, GREY, RED]
        for i, (col, lbl) in enumerate(zip(p3_pin_colors, p3_pin_labels)):
            x = 318 + i * 26
            y = 48
            c.setFillColor(col)
            c.setStrokeColor(colors.white)
            c.setLineWidth(0.5)
            c.circle(x, y, 9, fill=1, stroke=1)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 5)
            c.drawCentredString(x, y + 3, f"{i+1}")
            c.setFillColor(col)
            c.setFont("Helvetica", 5)
            c.drawCentredString(x, y - 4, lbl)

        # ── Power supplies callout ───────────────────────────────────────────
        c.setFillColor(colors.HexColor("#1a0000"))
        c.setStrokeColor(RED)
        c.setLineWidth(1)
        c.roundRect(5, 10, 120, 30, 4, fill=1, stroke=1)
        c.setFillColor(RED)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(10, 32, "⚠  External PSU required:")
        c.setFillColor(GOLD)
        c.setFont("Helvetica", 6)
        c.drawString(10, 23, "AVDD3: +3.3 V / 500 mA  |  AVDD1: −5.0 V / 200 mA")


class SpiTimingDiagram(Flowable):
    """SPI Mode 0 timing waveform diagram."""
    W, H = 480, 160

    def wrap(self, *args):
        return self.W, self.H

    def draw(self):
        c = self.canv
        W, H = self.W, self.H

        # Background
        c.setFillColor(colors.HexColor("#0d1a2a"))
        c.rect(0, 0, W, H, fill=1, stroke=0)

        sig_names = ["CSB", "SCLK", "MOSI", "MISO"]
        sig_colors = [GREY, YELLOW, ORANGE, GREEN]
        y_centers = [135, 100, 65, 30]
        h_sig = 14

        # Signal name column
        c.setFillColor(colors.HexColor("#0d2137"))
        c.rect(0, 0, 38, H, fill=1, stroke=0)
        for name, col, yc in zip(sig_names, sig_colors, y_centers):
            c.setFillColor(col)
            c.setFont("Helvetica-Bold", 7)
            c.drawRightString(36, yc - 3, name)

        # --- CSB waveform ---
        c.setStrokeColor(GREY)
        c.setLineWidth(1.5)
        p = c.beginPath()
        p.moveTo(40, 135 + h_sig)
        p.lineTo(80, 135 + h_sig)
        p.lineTo(80, 135 - h_sig)
        p.lineTo(430, 135 - h_sig)
        p.lineTo(430, 135 + h_sig)
        p.lineTo(470, 135 + h_sig)
        c.drawPath(p, stroke=1, fill=0)

        # --- SCLK waveform (24 half-cycles squeezed into 350px) ---
        c.setStrokeColor(YELLOW)
        c.setLineWidth(1.5)
        p = c.beginPath()
        p.moveTo(40, 100 - h_sig)
        p.lineTo(90, 100 - h_sig)
        # 12 full cycles, each 28px wide
        x = 90
        for _ in range(12):
            p.lineTo(x, 100 - h_sig)
            p.lineTo(x, 100 + h_sig)
            p.lineTo(x + 14, 100 + h_sig)
            p.lineTo(x + 14, 100 - h_sig)
            p.lineTo(x + 28, 100 - h_sig)
            x += 28
        p.lineTo(470, 100 - h_sig)
        c.drawPath(p, stroke=1, fill=0)

        # --- MOSI waveform (示: first bits = 0, bit 4 = 1, last = 1) ---
        c.setStrokeColor(ORANGE)
        c.setLineWidth(1.5)
        p = c.beginPath()
        p.moveTo(40, 65 - h_sig)
        p.lineTo(90, 65 - h_sig)
        # 8 zero bits, 1 one bit, 2 zero bits, 1 one bit
        # approximate with blocks
        p.lineTo(90, 65 + h_sig)
        p.lineTo(258, 65 + h_sig)   # 6 zeros high
        p.lineTo(258, 65 - h_sig)
        p.lineTo(314, 65 - h_sig)   # 1 one low (inverted for illustration)
        p.lineTo(314, 65 + h_sig)
        p.lineTo(378, 65 + h_sig)
        p.lineTo(378, 65 - h_sig)
        p.lineTo(426, 65 - h_sig)
        p.lineTo(426, 65 + h_sig)
        p.lineTo(470, 65 + h_sig)
        c.drawPath(p, stroke=1, fill=0)

        # MOSI bit field labels
        c.setFillColor(ORANGE)
        c.setFont("Helvetica", 5)
        c.drawCentredString(174, 82, "R/W + Rsvd + Addr[10:0]")
        c.drawCentredString(350, 68, "Data[7:0]")

        # --- MISO (high-Z shown as dashed) ---
        c.setStrokeColor(GREEN)
        c.setDash(4, 3)
        c.setLineWidth(1)
        c.line(40, 30, 470, 30)
        c.setDash()
        c.setFillColor(GREEN)
        c.setFont("Helvetica", 5.5)
        c.drawCentredString(255, 38, "SDO readback (enabled after Step 2)")

        # Annotations
        c.setFillColor(TEXT_DIM)
        c.setFont("Helvetica", 5.5)
        c.drawCentredString(60,  8, "Idle")
        c.drawCentredString(255, 8, "24 SCLK cycles  (24 bits, MSB first)")
        c.drawCentredString(450, 8, "Hold/Idle")

        # SCLK period brace
        c.setStrokeColor(YELLOW)
        c.setLineWidth(0.8)
        c.line(90, 114, 118, 114)
        c.line(90, 111, 90, 117)
        c.line(118, 111, 118, 117)
        c.setFillColor(YELLOW)
        c.setFont("Helvetica", 5)
        c.drawCentredString(104, 118, "T=80ns")


class RegisterTable(Flowable):
    """Draws the 12-step register sequence as a coloured vector table."""
    W, H = 480, 190

    STEPS = [
        ("1",  "0x000081", "0x000", "0x81", "Soft Reset",                     "Init & Reset",   "#64b5f6"),
        ("2",  "0x000018", "0x000", "0x18", "Enable SDO, 4-wire SPI mode",    "Init & Reset",   "#64b5f6"),
        ("3",  "0x040055", "0x400", "0x55", "Trim LDO to ≈1.8 V",            "Init & Reset",   "#64b5f6"),
        ("4",  "0x003860", "0x038", "0x60", "RAM Bypass — working registers", "RAM Bypass",     "#ce93d8"),
        ("5",  "0x002E7F", "0x02E", "0x7F", "RX Enable — all 4 channels",    "RAM Bypass",     "#ce93d8"),
        ("6",  "0x003408", "0x034", "0x08", "LNA Bias",                       "Bias & Switch",  "#80cbc4"),
        ("7",  "0x003516", "0x035", "0x16", "RX VGA / VM Bias",               "Bias & Switch",  "#80cbc4"),
        ("8",  "0x003120", "0x031", "0x20", "TR Switch → Receive mode",       "Bias & Switch",  "#80cbc4"),
        ("9",  "0x0010FF", "0x010", "0xFF", "RX Ch1 gain = maximum",          "Ch1 Config",     "#ff9800"),
        ("10", "0x001436", "0x014", "0x36", "RX Ch1 VM I = 0x36  (45°)",     "Ch1 Config",     "#ff9800"),
        ("11", "0x001536", "0x015", "0x36", "RX Ch1 VM Q = 0x36  (45°)",     "Ch1 Config",     "#ff9800"),
        ("12", "0x002801", "0x028", "0x01", "LDRX Override — commit to RF",   "Load/Commit",    "#4caf50"),
    ]

    def wrap(self, *args):
        return self.W, self.H

    def draw(self):
        c = self.canv
        # Header
        c.setFillColor(colors.HexColor("#1e3a6e"))
        c.rect(0, self.H - 14, self.W, 14, fill=1, stroke=0)
        c.setFillColor(ACCENT2)
        c.setFont("Helvetica-Bold", 6.5)
        for label, x in [("Step", 8), ("SPI Word", 30), ("Reg", 90),
                          ("Data", 120), ("Description", 150), ("Section", 390)]:
            c.drawString(x, self.H - 7, label)

        row_h = (self.H - 14) / 12
        for i, (step, word, reg, data, desc, sect, col) in enumerate(self.STEPS):
            y = self.H - 14 - (i + 1) * row_h
            bg = "#0d2137" if i % 2 == 0 else "#0a1e30"
            c.setFillColor(colors.HexColor(bg))
            c.rect(0, y, self.W, row_h, fill=1, stroke=0)

            c.setFillColor(colors.HexColor(col))
            c.setFont("Helvetica", 6)
            c.drawString(8,   y + row_h * 0.35, step)
            c.setFillColor(GOLD)
            c.setFont("Courier-Bold", 6)
            c.drawString(30,  y + row_h * 0.35, word)
            c.setFillColor(TEXT_DIM)
            c.setFont("Courier", 6)
            c.drawString(90,  y + row_h * 0.35, reg)
            c.drawString(120, y + row_h * 0.35, data)
            c.setFillColor(TEXT_MAIN)
            c.setFont("Helvetica", 6)
            c.drawString(150, y + row_h * 0.35, desc)
            c.setFillColor(colors.HexColor(col))
            c.setFont("Helvetica", 5.5)
            c.drawString(390, y + row_h * 0.35, sect)


class SpiWordFormat(Flowable):
    """Draws the 24-bit SPI word format diagram."""
    W, H = 480, 80

    def wrap(self, *args):
        return self.W, self.H

    def draw(self):
        c = self.canv
        c.setFillColor(colors.HexColor("#0d1a2a"))
        c.rect(0, 0, self.W, self.H, fill=1, stroke=0)

        # Four fields: R/W (1), Reserved (4), Addr (11), Data (8)
        fields = [
            (0,   8,   "R/W",     "0",         "#ce93d8",  "1 bit"),
            (8,   32,  "Reserved","0000",       "#4dd0e1",  "4 bits"),
            (32,  120, "Address", "addr[10:0]", "#ff9800",  "11 bits"),
            (120, 64,  "Data",    "data[7:0]",  "#4caf50",  "8 bits"),
        ]

        x = 0
        for x_off, w, name, val, col, sz in fields:
            c.setFillColor(colors.HexColor(col))
            c.setStrokeColor(colors.HexColor(col))
            c.setLineWidth(1.5)
            c.roundRect(x + 2, 20, w - 4, 38, 3, fill=0, stroke=1)
            c.setFillColor(colors.HexColor(col))
            c.setFont("Helvetica-Bold", 7 if w > 32 else 6)
            c.drawCentredString(x + w // 2, 48, name)
            c.setFillColor(GOLD)
            c.setFont("Courier-Bold", 8 if w > 32 else 7)
            c.drawCentredString(x + w // 2, 35, val)
            c.setFillColor(TEXT_DIM)
            c.setFont("Helvetica", 5.5)
            c.drawCentredString(x + w // 2, 15, sz)
            x += w

        # bit number labels
        c.setFillColor(TEXT_DIM)
        c.setFont("Helvetica", 5)
        c.drawCentredString(4,    66, "23")
        c.drawCentredString(44,   66, "22")
        c.drawCentredString(72,   66, "19")
        c.drawCentredString(96,   66, "18")
        c.drawCentredString(208,  66, "8")
        c.drawCentredString(240,  66, "7")
        c.drawCentredString(464,  66, "0")

        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(240, 73, "Example: addr=0x010, data=0xFF  →  0x0010FF  (RX Ch1 Max Gain)")


# ─────────────────────────────────────────────────────────────────────────────
# Build the PDF
# ─────────────────────────────────────────────────────────────────────────────

def build_pdf(out_path: str):
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=20*mm, bottomMargin=15*mm,
        title="ADAR1000 + ZC702 Setup Guide",
        author="Adar1000_testing",
        subject="SPI Interface Wiring Diagram and Configuration Guide",
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=26,
        textColor=colors.HexColor("#5bc0eb"),
        spaceAfter=6,
    )
    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#a0c4ff"),
        spaceAfter=4,
        spaceBefore=10,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#64b5f6"),
        spaceAfter=3,
        spaceBefore=6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#d0d8e8"),
        spaceAfter=3,
    )
    note_style = ParagraphStyle(
        "Note",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#ffd54f"),
        leftIndent=10,
        spaceAfter=4,
    )
    mono_style = ParagraphStyle(
        "Mono",
        parent=styles["Code"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#d0e8d0"),
        leftIndent=8,
        spaceAfter=2,
    )
    caption_style = ParagraphStyle(
        "Caption",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#7090a0"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    story = []

    # ── Cover / Title ────────────────────────────────────────────────────────
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        "ADAR1000-EVALZ ↔ ZC702 FPGA<br/>SPI Interface Setup Guide",
        title_style
    ))
    story.append(Paragraph(
        "PMOD J63 (ZC702) → P3 PMOD (ADAR1000-EVALZ) · RX1 Maximum Gain · 45° Phase Shift",
        caption_style
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#1e4a80"), spaceAfter=6))

    story.append(Paragraph(
        "This document provides a complete step-by-step guide to connecting the "
        "<b>ADAR1000-EVALZ</b> 4-channel X/Ku-band beamformer board to the "
        "<b>Xilinx ZC702</b> evaluation board (XC7Z020) using the <b>PMOD J63</b> "
        "connector and the <b>P3 PMOD</b> header on the ADAR1000-EVALZ. "
        "It covers the hardware wiring, SPI protocol, the 12-step "
        "<b>RX1_MaxG_45</b> register-write sequence, FPGA implementation flow, "
        "and expected VNA measurement results.",
        body_style
    ))
    story.append(Spacer(1, 4*mm))

    # ── Hardware Required table ───────────────────────────────────────────────
    story.append(Paragraph("1. Hardware Required", h1_style))
    hw_data = [
        ["Item", "Qty", "Notes"],
        ["Xilinx ZC702 Evaluation Board", "1", "XC7Z020-CLG484-1"],
        ["ADAR1000-EVALZ Board", "1", "Analog Devices beamformer eval board"],
        ["6-wire jumper cable (F-F)", "1", "Female-to-female, ≤150 mm"],
        ["External +3.3 V bench supply", "1", "AVDD3 rail, ≤500 mA"],
        ["External −5.0 V bench supply", "1", "AVDD1 rail, ≤200 mA"],
        ["USB micro-B cable", "1", "ZC702 JTAG / UART"],
        ["Vivado 2022.x or later", "—", "Free WebPACK edition sufficient"],
        ["VNA (optional)", "1", "8–16 GHz for RF verification"],
    ]
    hw_table = Table(hw_data, colWidths=[160, 30, 230])
    hw_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1e3a6e")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.HexColor("#a0c4ff")),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("LEADING",      (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#0d2137"), colors.HexColor("#0a1e30")]),
        ("TEXTCOLOR",    (0, 1), (-1, -1), colors.HexColor("#d0d8e8")),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#1e3a50")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(hw_table)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "⚠  The −5 V supply cannot be obtained from the ZC702 or the PMOD "
        "connector. A bench power supply or dedicated dc-dc converter is required.",
        note_style
    ))

    # ── Wiring diagram ───────────────────────────────────────────────────────
    story.append(Paragraph("2. Wiring Diagram", h1_style))
    story.append(Paragraph(
        "Connect the six wires between <b>ZC702 PMOD J63</b> and "
        "<b>ADAR1000-EVALZ P3</b> as shown in the diagram below. "
        "Always connect GND first and disconnect power before making changes.",
        body_style
    ))
    story.append(Spacer(1, 2*mm))

    wd = WiringDiagram()
    story.append(wd)
    story.append(Paragraph(
        "Figure 1 — Hardware wiring diagram: ZC702 J63 ↔ ADAR1000-EVALZ P3",
        caption_style
    ))

    # ── Wire-by-wire table ───────────────────────────────────────────────────
    story.append(Paragraph("2.1  Wire-by-Wire Connection Table", h2_style))
    wire_data = [
        ["#", "Colour", "ZC702 J63 Pin", "FPGA Pin", "ADAR1000 P3 Pin", "Signal"],
        ["1", "Yellow", "Pin 1",  "AB14", "Pin 4", "SCLK — SPI clock"],
        ["2", "Orange", "Pin 2",  "AA14", "Pin 2", "SDIO — MOSI (FPGA→ADAR1000)"],
        ["3", "Green",  "Pin 3",  "AA13", "Pin 3", "SDO — MISO (ADAR1000→FPGA)"],
        ["4", "Blue",   "Pin 4",  "AB13", "Pin 1", "CSB1 — Chip Select (active-low)"],
        ["5", "Black",  "Pin 5",  "GND",  "Pin 5", "Ground"],
        ["6", "Red",    "Pin 6",  "3.3 V","Pin 6", "VCC — Logic supply"],
    ]
    wire_table = Table(wire_data, colWidths=[18, 45, 55, 50, 65, 165])
    wire_colors = [None, "#fdd835", "#ff9800", "#4caf50", "#64b5f6", "#90a4ae", "#ef5350"]
    wire_ts = TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1e3a6e")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.HexColor("#a0c4ff")),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("LEADING",      (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#0d2137"), colors.HexColor("#0a1e30")]),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#1e3a50")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ])
    for row_i, col_hex in enumerate(wire_colors[1:], start=1):
        wire_ts.add("TEXTCOLOR", (1, row_i), (1, row_i), colors.HexColor(col_hex))
        wire_ts.add("FONTNAME",  (1, row_i), (1, row_i), "Helvetica-Bold")
        wire_ts.add("TEXTCOLOR", (5, row_i), (5, row_i), colors.HexColor(col_hex))
    wire_table.setStyle(wire_ts)
    story.append(wire_table)
    story.append(Spacer(1, 4*mm))

    # ── Step-by-step procedure ───────────────────────────────────────────────
    story.append(Paragraph("3. Step-by-Step Connection Procedure", h1_style))
    steps = [
        ("Step 1 — Power OFF", "Turn off both boards and all bench supplies before connecting any wires."),
        ("Step 2 — Ground first",
         "Connect J63 Pin 5 (GND) → P3 Pin 5 (GND) with the black wire. "
         "This establishes a common reference before signal wires are attached."),
        ("Step 3 — SPI signals",
         "Connect the four SPI wires: SCLK (Yellow J63-1→P3-4), "
         "SDIO/MOSI (Orange J63-2→P3-2), SDO/MISO (Green J63-3→P3-3), "
         "CSB1 (Blue J63-4→P3-1)."),
        ("Step 4 — Logic VCC",
         "Connect J63 Pin 6 (3.3 V) → P3 Pin 6 (VCC) with the red wire. "
         "This powers the on-board level translators (3.3 V ↔ 1.8 V)."),
        ("Step 5 — External power",
         "Connect bench supplies: +3.3 V → AVDD3 (≤500 mA) and −5.0 V → AVDD1 (≤200 mA). "
         "Set current limits before applying power."),
        ("Step 6 — Program FPGA",
         "Open Vivado, create an RTL project with rtl/*.v and constraints/zc702_pmod_j63.xdc. "
         "Set SPI_CLK_DIV=4 (SCLK=12.5 MHz), RESET_WAIT_CYCLES=10000 (100 µs). "
         "Run Synthesis → Implementation → Generate Bitstream → Program Device."),
        ("Step 7 — Power-on sequence",
         "Apply AVDD3 and AVDD1 first. Then power on the ZC702 (12 V supply). "
         "Wait for the DONE LED. The ADAR1000 is configured automatically; "
         "led_done_o illuminates when all 12 SPI writes are complete."),
        ("Step 8 — VNA verification (optional)",
         "Connect a VNA between RF_IO and RX1 SMAs. Sweep 8–16 GHz. "
         "Expected: gain ≈ +10 dB, return loss < −10 dB, phase shift = 45° on Ch1."),
    ]
    for title, body in steps:
        story.append(Paragraph(f"<b>{title}</b>", h2_style))
        story.append(Paragraph(body, body_style))

    story.append(PageBreak())

    # ── SPI Protocol ─────────────────────────────────────────────────────────
    story.append(Paragraph("4. SPI Protocol Details", h1_style))

    # SPI word format diagram
    story.append(Paragraph("4.1  24-bit SPI Word Format", h2_style))
    story.append(SpiWordFormat())
    story.append(Paragraph(
        "Figure 2 — 24-bit SPI word layout: {R/W[23], Reserved[22:19], Addr[18:8], Data[7:0]}",
        caption_style
    ))
    story.append(Spacer(1, 2*mm))

    spi_params = [
        ["Parameter", "Value"],
        ["Transaction width", "24 bits"],
        ["Bit order", "MSB first (bit 23 → bit 0)"],
        ["SPI mode", "Mode 0  (CPOL=0, CPHA=0)"],
        ["Data sampled on", "Rising SCLK edge"],
        ["Data shifted on", "Falling SCLK edge"],
        ["Max SCLK (ADAR1000)", "50 MHz"],
        ["SCLK in this design", "12.5 MHz  (CLK_DIV=4, 100 MHz system clock)"],
        ["CSB polarity", "Active-low"],
        ["Logic levels", "3.3 V (FPGA) ↔ 1.8 V (ADAR1000 core, via level translators)"],
    ]
    spi_table = Table(spi_params, colWidths=[160, 258])
    spi_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1e3a6e")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.HexColor("#a0c4ff")),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("LEADING",      (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#0d2137"), colors.HexColor("#0a1e30")]),
        ("TEXTCOLOR",    (0, 1), (-1, -1), colors.HexColor("#d0d8e8")),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#1e3a50")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(spi_table)
    story.append(Spacer(1, 4*mm))

    # SPI timing diagram
    story.append(Paragraph("4.2  SPI Timing Diagram", h2_style))
    story.append(SpiTimingDiagram())
    story.append(Paragraph(
        "Figure 3 — SPI Mode 0 timing: CSB low → 24 SCLK cycles → CSB high. "
        "MOSI valid before rising edge; MISO sampled on rising edge.",
        caption_style
    ))

    # ── Register sequence ────────────────────────────────────────────────────
    story.append(Paragraph("5. RX1_MaxG_45 Register Sequence", h1_style))
    story.append(Paragraph(
        "The following 12 SPI write transactions configure the ADAR1000 for "
        "<b>RX Channel 1 at maximum gain with a 45° phase shift</b>. "
        "The sequence must be executed in the order shown. "
        "After Step 1 (Soft Reset) a mandatory delay of ≥100 µs must elapse "
        "before Step 2.",
        body_style
    ))
    story.append(Spacer(1, 2*mm))
    story.append(RegisterTable())
    story.append(Paragraph(
        "Figure 4 — RX1_MaxG_45 SPI register write sequence (12 transactions)",
        caption_style
    ))
    story.append(Spacer(1, 3*mm))

    # Detailed descriptions
    sections = [
        ("5.1  Section 1: Device Initialisation & Reset", [
            "<b>0x000081</b> (Reg 0x000, Data 0x81): Soft Reset. Sets SOFT_RESET bit; all registers return to default. Wait ≥100 µs.",
            "<b>0x000018</b> (Reg 0x000, Data 0x18): Enable SDO pin; select 4-wire SPI mode. SDO_ACTIVE=1 enables readback.",
            "<b>0x040055</b> (Reg 0x400, Data 0x55): LDO trim. Adjusts the internal bandgap to deliver a stable ≈1.8 V to the BiCMOS core.",
        ]),
        ("5.2  Section 2: RAM Bypass & Operating Mode", [
            "<b>0x003860</b> (Reg 0x038, Data 0x60): RAM Bypass. BEAM_RAM_BYPASS=1: chip reads phase/gain from working registers, not Beam RAM.",
            "<b>0x002E7F</b> (Reg 0x02E, Data 0x7F): Receive Enable. Enables LNA and receive signal path on all four channels.",
            "<b>0x003408</b> (Reg 0x034, Data 0x08): LNA Bias. Sets DC bias current for the Low-Noise Amplifiers.",
        ]),
        ("5.3  Section 3: Bias and Switch Control", [
            "<b>0x003516</b> (Reg 0x035, Data 0x16): RX Bias. Configures operating currents for VGAs and Vector Modulators.",
            "<b>0x003120</b> (Reg 0x031, Data 0x20): TR Switch. TR_SPI=1 overrides the external TR pin and forces receive mode.",
        ]),
        ("5.4  Section 4: Channel 1 Configuration", [
            "<b>0x0010FF</b> (Reg 0x010, Data 0xFF): RX Ch1 Max Gain. Data=0xFF (255): attenuator fully bypassed, VGA at maximum.",
            "<b>0x001436</b> (Reg 0x014, Data 0x36): RX Ch1 Vector Modulator I = 0x36. In-phase component of the complex weight.",
            "<b>0x001536</b> (Reg 0x015, Data 0x36): RX Ch1 Vector Modulator Q = 0x36. Quadrature component. Together I=Q=0x36 produces a 45° phase rotation.",
            "<b>0x002801</b> (Reg 0x028, Data 0x01): LDRX Override. LDRX_OVR=1 transfers all buffered gain/phase values to the active RF path. This is the commit step.",
        ]),
    ]
    for sec_title, items in sections:
        story.append(Paragraph(sec_title, h2_style))
        for item in items:
            story.append(Paragraph("• " + item, body_style))
        story.append(Spacer(1, 2*mm))

    story.append(PageBreak())

    # ── FPGA Implementation ───────────────────────────────────────────────────
    story.append(Paragraph("6. FPGA Implementation Flow (Vivado)", h1_style))
    impl_steps = [
        ("6.1 Create Project",
         "Open Vivado. New Project → RTL Project. "
         "Add all files from rtl/ directory: spi_master.v, adar1000_ctrl.v, top.v. "
         "Set top.v as the top-level module."),
        ("6.2 Add Constraints",
         "Add constraints/zc702_pmod_j63.xdc to the project. "
         "This file contains PACKAGE_PIN assignments for AB14/AA14/AA13/AB13 "
         "and I/O timing constraints."),
        ("6.3 Configure Clock",
         "Option A (PS clock): In a Zynq block design, add Clocking Wizard, "
         "set FCLK0=100 MHz, connect to top.clk port. "
         "Option B (PL-only): Use 200 MHz diff clock U64 with IBUFDS + MMCM "
         "to generate 100 MHz."),
        ("6.4 Set Parameters",
         "In top.v: SPI_CLK_DIV=4 → SCLK=12.5 MHz. "
         "RESET_WAIT_CYCLES=10000 → 100 µs post-reset delay at 100 MHz."),
        ("6.5 Run Flow",
         "Run Synthesis → Implementation → Generate Bitstream. "
         "Check timing report: all paths should be easily met at 100 MHz "
         "(SCLK is only 12.5 MHz)."),
        ("6.6 Program Device",
         "Open Hardware Manager, connect to ZC702 via USB-JTAG, "
         "program the .bit file. The ADAR1000 is configured automatically. "
         "led_done_o (DS12 or assigned LED) illuminates when done."),
    ]
    for title, body in impl_steps:
        story.append(Paragraph(f"<b>{title}</b>", h2_style))
        story.append(Paragraph(body, body_style))

    story.append(Spacer(1, 4*mm))

    # XDC snippet
    story.append(Paragraph("6.7  Key XDC Constraints (zc702_pmod_j63.xdc)", h2_style))
    xdc_lines = [
        "create_clock -period 10.000 -name clk [get_ports clk]",
        'set_property -dict { PACKAGE_PIN AB14  IOSTANDARD LVCMOS33 } [get_ports spi_sclk]',
        'set_property -dict { PACKAGE_PIN AA14  IOSTANDARD LVCMOS33 } [get_ports spi_mosi]',
        'set_property -dict { PACKAGE_PIN AA13  IOSTANDARD LVCMOS33 } [get_ports spi_miso]',
        'set_property -dict { PACKAGE_PIN AB13  IOSTANDARD LVCMOS33 } [get_ports spi_csb]',
    ]
    for line in xdc_lines:
        story.append(Paragraph(line, mono_style))

    story.append(Spacer(1, 4*mm))

    # ── Alternative J62 ───────────────────────────────────────────────────────
    story.append(Paragraph("7. Alternative: Using PMOD J62", h1_style))
    story.append(Paragraph(
        "If J63 is occupied, use J62. Replace the four PACKAGE_PIN entries in "
        "the XDC file with the J62 pin assignments below. All other constraints "
        "remain identical.",
        body_style
    ))
    j62_data = [
        ["Signal", "J62 FPGA Pin"],
        ["spi_sclk", "Y12"],
        ["spi_mosi", "W12"],
        ["spi_miso", "V12"],
        ["spi_csb",  "V13"],
    ]
    j62_table = Table(j62_data, colWidths=[120, 80])
    j62_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1e3a6e")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.HexColor("#a0c4ff")),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("LEADING",      (0, 0), (-1, -1), 12),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#0d2137"), colors.HexColor("#0a1e30")]),
        ("TEXTCOLOR",    (0, 1), (-1, -1), colors.HexColor("#d0d8e8")),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#1e3a50")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("FONTNAME",     (1, 1), (1, -1),  "Courier"),
    ]))
    story.append(j62_table)
    story.append(Spacer(1, 4*mm))

    # ── Troubleshooting ──────────────────────────────────────────────────────
    story.append(Paragraph("8. Troubleshooting", h1_style))
    trouble_data = [
        ["Symptom", "Likely Cause", "Fix"],
        ["led_done never asserts", "FPGA not programmed / rst_n stuck low",
         "Check JTAG connection, re-program, confirm reset logic"],
        ["No SCLK visible", "Wrong J63 pin",
         "Verify AB14 against board silk screen"],
        ["SPI visible, no RF output", "AVDD1 (−5 V) missing",
         "Check bench supply polarity and current limit"],
        ["Gain lower than expected", "LDO trim skipped",
         "Ensure all 12 steps execute; check spi_done signal"],
        ["CSB stays low", "SPI master stuck in SHIFT",
         "Check CLK_DIV parameter; verify SCLK and done signal"],
        ["Wrong phase on VNA", "LDRX not executed",
         "Confirm step 12 (0x002801) completes before measurement"],
    ]
    trouble_table = Table(trouble_data, colWidths=[130, 130, 158])
    trouble_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1e3a6e")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.HexColor("#a0c4ff")),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 7.5),
        ("LEADING",      (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#0d2137"), colors.HexColor("#0a1e30")]),
        ("TEXTCOLOR",    (0, 1), (-1, -1), colors.HexColor("#d0d8e8")),
        ("TEXTCOLOR",    (2, 1), (2, -1),  colors.HexColor("#4caf50")),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#1e3a50")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(trouble_table)
    story.append(Spacer(1, 4*mm))

    # ── Expected Results ─────────────────────────────────────────────────────
    story.append(Paragraph("9. Expected VNA Measurement Results", h1_style))
    story.append(Paragraph(
        "After executing the full <b>RX1_MaxG_45</b> configuration sequence, "
        "connect a Vector Network Analyzer between the <b>RF_IO</b> SMA port "
        "and the <b>RX1</b> SMA port on the ADAR1000-EVALZ and sweep from "
        "8 GHz to 16 GHz. The expected results are:",
        body_style
    ))
    results_data = [
        ["Measurement", "Expected Value", "Significance"],
        ["Insertion Gain (S21)", "≈ +10 dB at mid-band (8–16 GHz)",
         "Validates LNA + VGA at maximum gain setting"],
        ["Return Loss — RX1 (S11)", "< −10 dB across most of band",
         "Confirms good impedance matching at RX1 SMA"],
        ["Return Loss — RF_IO (S22)", "< −10 dB across most of band",
         "Confirms matching at the common port"],
        ["Phase — RX Channel 1", "45° (relative to 0° reference)",
         "Validates I/Q vector modulator settings 0x36/0x36"],
    ]
    results_table = Table(results_data, colWidths=[120, 150, 148])
    results_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1e3a6e")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.HexColor("#a0c4ff")),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("LEADING",      (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#0d2137"), colors.HexColor("#0a1e30")]),
        ("TEXTCOLOR",    (0, 1), (-1, -1), colors.HexColor("#d0d8e8")),
        ("TEXTCOLOR",    (1, 1), (1, -1),  colors.HexColor("#4caf50")),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#1e3a50")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(results_table)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "Note: The oscillatory behaviour in the measured return loss is "
        "characteristic of transmission-line effects and parasitic transitions "
        "in the evaluation board's SMA connectors and PCB traces. "
        "Maintaining return loss below −10 dB ensures reflections are minimised, "
        "preserving the phase and amplitude accuracy required for null steering.",
        body_style
    ))

    # ── File Reference ───────────────────────────────────────────────────────
    story.append(Paragraph("10. Repository File Reference", h1_style))
    file_ref = [
        ["File", "Description"],
        ["rtl/spi_master.v",      "24-bit SPI master, Mode 0, MSB-first, CLK_DIV parameter"],
        ["rtl/adar1000_ctrl.v",   "12-step RX1_MaxG_45 register-write sequencer"],
        ["rtl/top.v",             "Top-level: binds controller + SPI master to PMOD J63 ports"],
        ["sim/tb_spi_master.v",   "SPI master unit testbench (Icarus Verilog)"],
        ["sim/tb_adar1000_ctrl.v","Integration testbench with ADAR1000 slave model"],
        ["constraints/zc702_pmod_j63.xdc", "Vivado XDC: pin assignments + timing constraints"],
        ["scripts/RX1_MaxG_45.txt","Annotated SPI command script (hex words)"],
        ["docs/wiring_diagram.md","Markdown wiring guide with pin tables"],
        ["docs/wiring_diagram.svg","SVG colour wiring diagram"],
        ["docs/spi_timing.svg",   "SVG SPI Mode 0 timing diagram"],
        ["docs/system_block_diagram.svg","SVG system block diagram"],
        ["docs/register_map.svg", "SVG SPI word format and register map"],
        ["docs/ADAR1000_ZC702_Setup_Guide.pdf", "This PDF setup guide"],
    ]
    file_table = Table(file_ref, colWidths=[175, 243])
    file_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1e3a6e")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.HexColor("#a0c4ff")),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 7.5),
        ("LEADING",      (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#0d2137"), colors.HexColor("#0a1e30")]),
        ("TEXTCOLOR",    (0, 1), (-1, -1), colors.HexColor("#d0d8e8")),
        ("FONTNAME",     (0, 1), (0, -1),  "Courier"),
        ("TEXTCOLOR",    (0, 1), (0, -1),  colors.HexColor("#ffd54f")),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#1e3a50")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(file_table)

    # ── Build ────────────────────────────────────────────────────────────────
    def on_first_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#0f3460"))
        canvas.rect(0, A4[1] - 22, A4[0], 22, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#a0c4ff"))
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawCentredString(A4[0] / 2, A4[1] - 14,
                                 "ADAR1000-EVALZ ↔ ZC702 FPGA — SPI Interface Setup Guide")
        canvas.setFillColor(colors.HexColor("#0f3460"))
        canvas.rect(0, 0, A4[0], 16, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#607080"))
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(A4[0] / 2, 5, f"Page {doc.page}")
        canvas.restoreState()

    def on_later_pages(canvas, doc):
        on_first_page(canvas, doc)

    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    print(f"PDF written: {out_path}")


if __name__ == "__main__":
    build_pdf(OUT_PATH)
