"""Module 12: PDF Report Generator using ReportLab.

Produces a publication-quality, enterprise-styled PDF document documenting export
integrity, cryptographic evidence, anomalies, and recovery assessment.
"""

from pathlib import Path
from typing import Optional, Union
import io

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from dbguard.models import (
    AnalysisReport,
    RecoveryClassification,
    VerificationStatus,
)
from dbguard.utils.safe_paths import safe_output_path


def generate_pdf_report(report: AnalysisReport, output_path: Union[str, Path]) -> Path:
    """Render a comprehensive PDF report using ReportLab.

    Args:
        report: AnalysisReport instance.
        output_path: Destination PDF filepath.

    Returns:
        Resolved Path to the created PDF file.
    """
    dest = safe_output_path(output_path, allow_overwrite=True)

    doc = SimpleDocTemplate(
        str(dest),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        alignment=0
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b")
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=body_style,
        fontName="Helvetica-Bold"
    )
    badge_style = ParagraphStyle(
        "Badge",
        parent=styles["Normal"],
        fontSize=13,
        leading=16,
        fontName="Helvetica-Bold",
        alignment=1
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("DBGuard — Export Integrity Assessment Report", title_style))
    story.append(Paragraph(
        f"Automated Non-Restorative Verification • Generated: {report.generated_at_utc} UTC • Report ID: {report.report_id}",
        subtitle_style
    ))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceAfter=14))

    # 2. Executive Recovery Verdict Box
    rec_class = report.recovery_assessment.classification
    if rec_class == RecoveryClassification.VERIFIED_WITHIN_SCOPE:
        badge_bg = colors.HexColor("#dcfce7")
        badge_color = colors.HexColor("#166534")
    elif rec_class in (RecoveryClassification.LIKELY_USABLE_BUT_NOT_FULLY_VERIFIED, RecoveryClassification.RECOVERY_POSSIBLE_WITH_ERRORS):
        badge_bg = colors.HexColor("#fef3c7")
        badge_color = colors.HexColor("#92400e")
    else:
        badge_bg = colors.HexColor("#fee2e2")
        badge_color = colors.HexColor("#991b1b")

    badge_p = Paragraph(f"<font color='{badge_color}'>{rec_class.value}</font>", badge_style)
    summary_p = Paragraph(f"<b>Assessment:</b> {report.recovery_assessment.summary}", body_style)

    badge_table = Table([[badge_p], [summary_p]], colWidths=[530])
    badge_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), badge_bg),
        ("BOX", (0, 0), (-1, -1), 1, badge_color),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 14))

    # 3. File & Physical Stream Verification Table
    story.append(Paragraph("1. Physical Compression Stream Verification", h2_style))
    comp = report.compression_validation
    fi = report.file_inspection
    stream_data = [
        [Paragraph("Target File", body_bold), Paragraph(fi.filename, body_style), Paragraph("Detected Format", body_bold), Paragraph(fi.detected_compression.value.upper(), body_style)],
        [Paragraph("Compressed Size", body_bold), Paragraph(f"{fi.file_size_bytes:,} bytes", body_style), Paragraph("Decompressed Size", body_bold), Paragraph(f"{comp.decompressed_bytes:,} bytes", body_style)],
        [Paragraph("Expansion Ratio", body_bold), Paragraph(f"{comp.expansion_ratio:.2f}x", body_style), Paragraph("Stream Integrity", body_bold), Paragraph(f"<b>{comp.status.value}</b>", body_style)],
        [Paragraph("CRC / Trailer Valid", body_bold), Paragraph(str(comp.crc_or_trailer_valid), body_style), Paragraph("Stream Truncated", body_bold), Paragraph(str(comp.is_truncated), body_style)],
    ]
    t1 = Table(stream_data, colWidths=[110, 155, 110, 155])
    t1.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t1)
    story.append(Spacer(1, 12))

    # 4. Data Records & Structural Parsing Table
    story.append(Paragraph("2. Incremental Data Parsing & Schema Assessment", h2_style))
    pr = report.parsing_result
    parse_data = [
        [Paragraph("Data Format", body_bold), Paragraph(pr.format.value.upper(), body_style), Paragraph("Parsing Status", body_bold), Paragraph(f"<b>{pr.status.value}</b>", body_style)],
        [Paragraph("Data Rows Parsed", body_bold), Paragraph(f"<b>{pr.record_count:,}</b>", body_style), Paragraph("Table Columns", body_bold), Paragraph(f"{pr.column_count}", body_style)],
        [Paragraph("Malformed Rows", body_bold), Paragraph(f"{pr.malformed_record_count:,}", body_style), Paragraph("Empty / Null Cells", body_bold), Paragraph(f"{pr.empty_value_count:,}", body_style)],
        [Paragraph("Schema Fingerprint", body_bold), Paragraph(f"<font size=7>{pr.schema_fingerprint}</font>", body_style), Paragraph("Recoverable Rows Est.", body_bold), Paragraph(f"{report.recovery_assessment.recoverable_record_estimate:,}", body_style)],
    ]
    t2 = Table(parse_data, colWidths=[110, 155, 110, 155])
    t2.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t2)
    story.append(Spacer(1, 12))

    # 5. Cryptographic Evidence
    story.append(Paragraph("3. Multi-Granularity Cryptographic Checksums", h2_style))
    hr = report.hash_result
    hash_data = [
        [Paragraph("Compressed SHA-256", body_bold), Paragraph(f"<font size=7>{hr.compressed_sha256}</font>", body_style)],
        [Paragraph("Decompressed SHA-256", body_bold), Paragraph(f"<font size=7>{hr.decompressed_sha256 or 'N/A'}</font>", body_style)],
        [Paragraph("Chunk Merkle Root", body_bold), Paragraph(f"<font size=7>{hr.merkle_root or 'N/A'}</font>", body_style)],
        [Paragraph("1MB Chunks Verified", body_bold), Paragraph(f"{len(hr.chunk_hashes)} chunks calculated", body_style)],
    ]
    t3 = Table(hash_data, colWidths=[140, 390])
    t3.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t3)
    story.append(Spacer(1, 12))

    # 6. Trusted Manifest Verification (if applicable)
    if report.manifest_verification:
        mv = report.manifest_verification
        story.append(Paragraph("4. Trusted Manifest Concordance", h2_style))
        man_rows = [
            [Paragraph("Check", body_bold), Paragraph("Status", body_bold), Paragraph("Expected", body_bold), Paragraph("Observed", body_bold), Paragraph("Message", body_bold)]
        ]
        for c in mv.checks:
            man_rows.append([
                Paragraph(c.field_name, body_style),
                Paragraph(f"<b>{c.status.value}</b>", body_style),
                Paragraph(str(c.expected)[:24], body_style),
                Paragraph(str(c.observed)[:24], body_style),
                Paragraph(c.message, body_style)
            ])
        t_man = Table(man_rows, colWidths=[90, 65, 80, 80, 215])
        t_man.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_man)
        story.append(Spacer(1, 12))

    # 7. Detected Anomalies Table
    story.append(Paragraph(f"5. Detected Anomalies ({len(report.anomalies)})", h2_style))
    if report.anomalies:
        anom_rows = [
            [Paragraph("Rule", body_bold), Paragraph("Severity", body_bold), Paragraph("Observed Value", body_bold), Paragraph("Explanation & Root Cause", body_bold)]
        ]
        for a in report.anomalies:
            anom_rows.append([
                Paragraph(a.rule_id, body_style),
                Paragraph(f"<b>{a.severity.value}</b>", body_style),
                Paragraph(str(a.observed_value), body_style),
                Paragraph(a.explanation, body_style)
            ])
        t_anom = Table(anom_rows, colWidths=[120, 65, 110, 235])
        t_anom.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fee2e2")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_anom)
    else:
        story.append(Paragraph("<i>No structural or metric anomalies detected.</i>", body_style))
    story.append(Spacer(1, 12))

    # 8. Scientific Caveats & Recommendations
    story.append(Paragraph("6. Scientific Caveats and Recovery Guidance", h2_style))
    caveats = (
        "<b>Important Integrity Limitations:</b><br/>"
        "• <b>Compression != Completeness:</b> Complete decompression verifies that the physical archive format is intact, but "
        "cannot prove that the database export process included all rows from the source table.<br/>"
        "• <b>Compression Ratio Variations:</b> File size reductions despite row count growth often reflect legitimate data dynamics "
        "(e.g. repeated values, nullable columns, shorter strings, or dictionary efficiency) rather than corruption.<br/>"
        "• <b>Trust Boundary:</b> Hashes computed post-hoc from an existing export verify subsequent immutability but cannot prove "
        "historical source fidelity without a manifest created synchronously at export time."
    )
    story.append(Paragraph(caveats, body_style))
    story.append(Spacer(1, 8))

    recs = "<b>Actionable Recommendations:</b><br/>" + "<br/>".join(
        f"• {act}" for act in report.recovery_assessment.recommended_actions
    )
    story.append(Paragraph(recs, body_style))

    # Build PDF
    doc.build(story)
    return dest

