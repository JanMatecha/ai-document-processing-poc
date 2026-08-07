#!/usr/bin/env python3
"""Generate the deterministic technical PDF used by the first PoC."""

from __future__ import annotations

from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESTINATION = PROJECT_ROOT / "input" / "test.pdf"
NAVY = colors.HexColor("#17365D")
BLUE = colors.HexColor("#D9EAF7")
LIGHT_BLUE = colors.HexColor("#EEF5FA")
ORANGE = colors.HexColor("#E87722")
GREY = colors.HexColor("#555555")


def page_header_footer(canvas, document) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#9AA7B2"))
    canvas.setLineWidth(0.4)
    canvas.line(18 * mm, height - 15 * mm, width - 18 * mm, height - 15 * mm)
    canvas.setFillColor(GREY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, height - 11.5 * mm, "THERMAL CONTROL MODULE / TS-042")
    canvas.drawRightString(width - 18 * mm, 11 * mm, f"Page {document.page}")
    canvas.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
    canvas.restoreState()


def flow_diagram() -> Drawing:
    drawing = Drawing(470, 105)
    boxes = [
        (8, "Temperature\nsensor"),
        (166, "PID\ncontroller"),
        (324, "Power\nstage"),
    ]
    for x, label in boxes:
        drawing.add(Rect(x, 34, 128, 52, rx=4, ry=4, fillColor=LIGHT_BLUE, strokeColor=NAVY))
        first, second = label.split("\n")
        drawing.add(String(x + 64, 61, first, fontName="Helvetica-Bold", fontSize=10, textAnchor="middle"))
        drawing.add(String(x + 64, 47, second, fontName="Helvetica", fontSize=9, textAnchor="middle"))
    for start, end in [(136, 166), (294, 324)]:
        drawing.add(Line(start, 60, end, 60, strokeColor=ORANGE, strokeWidth=2))
        drawing.add(Line(end - 7, 65, end, 60, strokeColor=ORANGE, strokeWidth=2))
        drawing.add(Line(end - 7, 55, end, 60, strokeColor=ORANGE, strokeWidth=2))
    drawing.add(String(230, 10, "Figure 1 - Closed-loop thermal control signal path", fontName="Helvetica-Oblique", fontSize=9, textAnchor="middle", fillColor=GREY))
    return drawing


def build_pdf(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DocumentTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=6 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=NAVY,
            spaceBefore=5 * mm,
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyTechnical",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceAfter=2.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallTechnical",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
        )
    )
    styles.add(
        ParagraphStyle(
            name="NoteHeading",
            parent=styles["SmallTechnical"],
            fontName="Helvetica-Bold",
            textColor=colors.white,
        )
    )

    document = SimpleDocTemplate(
        str(destination),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=22 * mm,
        bottomMargin=21 * mm,
        title="Thermal Control Module - Test Specification",
        author="Document Ingestion PoC",
        subject="Technical PDF fixture for MarkItDown and Docling comparison",
        invariant=1,
    )

    story = [
        Paragraph("Thermal Control Module", styles["DocumentTitle"]),
        Paragraph("Verification Test Specification", ParagraphStyle(
            "SubtitleTechnical", parent=styles["Heading2"], alignment=TA_CENTER,
            fontName="Helvetica", fontSize=13, textColor=GREY, spaceAfter=7 * mm,
        )),
    ]

    metadata = [
        ["Document ID", "TS-042", "Revision", "1.3"],
        ["Status", "Released", "Test date", "2026-08-07"],
        ["Owner", "Systems Engineering", "Classification", "Internal test fixture"],
    ]
    metadata_table = Table(metadata, colWidths=[27 * mm, 52 * mm, 28 * mm, 54 * mm])
    metadata_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), BLUE),
        ("BACKGROUND", (2, 0), (2, -1), BLUE),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#20252A")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8FA1B2")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([
        metadata_table,
        Paragraph("1. Scope", styles["Section"]),
        Paragraph(
            "This specification defines the bench tests for a 24 V closed-loop thermal "
            "control module. The module regulates an aluminium test plate between 20 and "
            "80 degrees C while reporting temperature, supply current, and fault status.",
            styles["BodyTechnical"],
        ),
        Paragraph("2. System overview", styles["Section"]),
        Paragraph(
            "The test article contains three functional blocks. Their signal flow is shown "
            "below; arrows indicate the intended reading direction from left to right.",
            styles["BodyTechnical"],
        ),
        flow_diagram(),
        Paragraph("Key interfaces", styles["Heading3"]),
        Paragraph("- Sensor input: Pt1000, four-wire connection", styles["BodyTechnical"]),
        Paragraph("- Power input: 24 V DC nominal, 6 A maximum", styles["BodyTechnical"]),
        Paragraph("- Data interface: isolated RS-485 at 115200 bit/s", styles["BodyTechnical"]),
        Paragraph("3. Control model", styles["Section"]),
        Paragraph(
            "The expected steady-state heat balance is expressed by "
            "<font name='Courier-Bold'>Q = m * c_p * Delta T</font>. Controller efficiency "
            "is calculated as <font name='Courier-Bold'>eta = P_load / P_input</font>.",
            styles["BodyTechnical"],
        ),
        KeepTogether([
            Table(
                [[Paragraph("Engineering note", styles["NoteHeading"])],
                 [Paragraph(
                     "Measurements are valid only after the plate-temperature slope remains "
                     "below 0.1 degrees C per minute for five consecutive minutes.",
                     styles["SmallTechnical"],
                 )]],
                colWidths=[161 * mm],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BACKGROUND", (0, 1), (-1, 1), LIGHT_BLUE),
                    ("BOX", (0, 0), (-1, -1), 0.8, NAVY),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]),
            )
        ]),
        PageBreak(),
        Paragraph("4. Performance measurements", styles["Section"]),
        Paragraph(
            "Table 1 contains the reference measurements captured at five operating points. "
            "Numeric values use SI-compatible units and a decimal point.",
            styles["BodyTechnical"],
        ),
    ])

    measurements = [
        ["Test point", "Ambient\n(deg C)", "Input\n(V)", "Load\n(A)", "Plate\n(deg C)", "Efficiency\n(%)"],
        ["TP-01", "20.1", "24.02", "1.20", "30.0", "91.2"],
        ["TP-02", "20.0", "24.01", "2.35", "40.0", "92.8"],
        ["TP-03", "22.4", "23.98", "3.60", "55.0", "93.5"],
        ["TP-04", "25.2", "23.96", "4.80", "70.0", "92.9"],
        ["TP-05", "25.0", "23.94", "5.50", "80.0", "91.7"],
    ]
    measurement_table = Table(
        measurements,
        colWidths=[29 * mm, 28 * mm, 25 * mm, 24 * mm, 28 * mm, 27 * mm],
        repeatRows=1,
    )
    measurement_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#7E8B96")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([
        measurement_table,
        Paragraph("Table 1 - Thermal performance at nominal supply voltage", ParagraphStyle(
            "TableCaption", parent=styles["SmallTechnical"], alignment=TA_CENTER,
            textColor=GREY, spaceBefore=2 * mm, spaceAfter=4 * mm,
        )),
        Paragraph("5. Verification procedure", styles["Section"]),
        Paragraph("1. Inspect the wiring and confirm protective-earth continuity.", styles["BodyTechnical"]),
        Paragraph("2. Apply 24 V DC with the current limit set to 6 A.", styles["BodyTechnical"]),
        Paragraph("3. Command each plate-temperature setpoint in ascending order.", styles["BodyTechnical"]),
        Paragraph("4. Wait for the stability condition defined in Section 3.", styles["BodyTechnical"]),
        Paragraph("5. Record voltage, current, plate temperature, and fault status.", styles["BodyTechnical"]),
        Paragraph("6. Acceptance criteria", styles["Section"]),
    ])

    acceptance = [
        ["Requirement", "Limit", "Result"],
        ["Temperature error", "+/- 1.0 deg C", "Pass if every point complies"],
        ["Input voltage", "23.5 to 24.5 V", "Pass if no dropout occurs"],
        ["Efficiency", ">= 90.0%", "Pass if measured after stabilization"],
        ["Communication", "0 frame errors", "Pass over 10,000 frames"],
    ]
    acceptance_table = Table(acceptance, colWidths=[52 * mm, 44 * mm, 65 * mm])
    acceptance_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3E5F7D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#7E8B96")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([
        acceptance_table,
        Paragraph("7. Expected reading order", styles["Section"]),
        Paragraph(
            "A correct conversion reads Sections 4 through 7 in sequence, keeps each table "
            "row intact, and places this final paragraph after the acceptance table.",
            styles["BodyTechnical"],
        ),
    ])

    document.build(story, onFirstPage=page_header_footer, onLaterPages=page_header_footer)


if __name__ == "__main__":
    build_pdf(DESTINATION)
    print(f"Created {DESTINATION}")
