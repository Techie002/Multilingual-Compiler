import os
import csv
import io
import time
import html
import datetime

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted, KeepTogether, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'reports')

def generate_pdf_report(submission_data, user_data, assignment_data, evaluation_data=None):
    """
    Generates a professional PDF report summarizing submission evaluation, score breakdown,
    test case results, performance metrics, and source code.
    Returns the absolute path to the generated PDF file.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    sub_id = submission_data.get('id', 0)
    filename = f"report_sub_{sub_id}_{int(time.time())}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    if HAS_REPORTLAB:
        try:
            _generate_reportlab_pdf(filepath, submission_data, user_data, assignment_data, evaluation_data)
            return filepath
        except Exception as e:
            print(f"[PDF Generator] ReportLab generation encountered an error: {e}. Falling back to standard binary PDF generator.")

    # Fallback to pure Python binary PDF generator (100% valid PDF-1.4 spec)
    _generate_pure_pdf(filepath, submission_data, user_data, assignment_data, evaluation_data)
    return filepath

def _generate_reportlab_pdf(filepath, submission_data, user_data, assignment_data, evaluation_data):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()
    elements = []

    # Custom Palette
    primary_color = colors.HexColor('#4f46e5')     # Indigo
    dark_color = colors.HexColor('#0f172a')        # Slate 900
    text_color = colors.HexColor('#334155')        # Slate 700
    light_bg = colors.HexColor('#f8fafc')          # Slate 50
    border_color = colors.HexColor('#cbd5e1')      # Slate 300
    success_color = colors.HexColor('#059669')     # Emerald 600
    accent_amber = colors.HexColor('#d97706')      # Amber 600
    code_bg = colors.HexColor('#1e293b')           # Dark Slate

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=12
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=dark_color,
        spaceBefore=10,
        spaceAfter=6
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=dark_color
    )
    cell_normal = ParagraphStyle(
        'CellNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=text_color
    )
    code_style = ParagraphStyle(
        'CodeText',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#f8fafc')
    )

    # 1. Header Banner
    now_str = datetime.datetime.now().strftime("%B %d, %Y - %H:%M:%S UTC")
    elements.append(Paragraph("CodeVision AI — Automated Evaluation Report", title_style))
    elements.append(Paragraph(f"Official Submission Benchmark & Code Quality Audit &bull; Generated: {now_str}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=2, spaceAfter=12))

    # 2. Student & Assignment Overview Table
    student_name = user_data.get('username', 'N/A')
    student_email = user_data.get('email', 'N/A')
    assign_title = assignment_data.get('title', 'Sandbox IDE Submission') if assignment_data else 'Sandbox IDE Submission'
    language = str(submission_data.get('language', 'N/A')).upper()
    sub_id = str(submission_data.get('id', 'N/A'))
    sub_date = submission_data.get('created_at', now_str)

    meta_table_data = [
        [
            Paragraph("<b>Student Name:</b>", cell_bold), Paragraph(student_name, cell_normal),
            Paragraph("<b>Submission ID:</b>", cell_bold), Paragraph(f"#{sub_id}", cell_normal)
        ],
        [
            Paragraph("<b>Student Email:</b>", cell_bold), Paragraph(student_email, cell_normal),
            Paragraph("<b>Language:</b>", cell_bold), Paragraph(f"<font color='#4f46e5'><b>{language}</b></font>", cell_normal)
        ],
        [
            Paragraph("<b>Assignment:</b>", cell_bold), Paragraph(assign_title, cell_normal),
            Paragraph("<b>Timestamp:</b>", cell_bold), Paragraph(sub_date, cell_normal)
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[90, 180, 90, 172])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 12))

    # 3. Score Breakdown & Performance Metrics
    score = submission_data.get('score', 0)
    correctness_score = submission_data.get('correctness_score', 0)
    style_score = submission_data.get('style_score', 0)
    exec_time = submission_data.get('execution_time', 0.0)
    memory_mb = submission_data.get('memory_usage', 0.0)
    ai_prob = submission_data.get('ai_probability_score', 0.0)

    score_color = '#059669' if score >= 80 else ('#d97706' if score >= 50 else '#dc2626')

    elements.append(Paragraph("Performance & Evaluation Metrics", section_title))
    metrics_data = [
        [
            Paragraph("<b>Overall Evaluation Score:</b>", cell_bold),
            Paragraph(f"<font size=12 color='{score_color}'><b>{score} / 100</b></font>", cell_bold),
            Paragraph("<b>Execution Time:</b>", cell_bold),
            Paragraph(f"{exec_time} seconds", cell_normal)
        ],
        [
            Paragraph("<b>Test Cases Correctness:</b>", cell_bold),
            Paragraph(f"{correctness_score} / 100 pts", cell_normal),
            Paragraph("<b>Memory Peak:</b>", cell_bold),
            Paragraph(f"{memory_mb} MB", cell_normal)
        ],
        [
            Paragraph("<b>Code Quality & Style:</b>", cell_bold),
            Paragraph(f"{style_score} / 100 pts", cell_normal),
            Paragraph("<b>AI Probability:</b>", cell_bold),
            Paragraph(f"{ai_prob}%", cell_normal)
        ]
    ]
    metrics_table = Table(metrics_data, colWidths=[140, 130, 130, 132])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 10))

    # 4. Evaluation Feedback
    feedback_text = "Evaluation completed successfully."
    if evaluation_data and evaluation_data.get('feedback'):
        feedback_text = evaluation_data.get('feedback')
    elif submission_data.get('output'):
        feedback_text = submission_data.get('output')

    feedback_para = Paragraph(f"<b>Evaluator Feedback:</b> {html.escape(feedback_text)}", cell_normal)
    feedback_box = Table([[feedback_para]], colWidths=[532])
    feedback_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#e0f2fe')),
        ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#38bdf8')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(feedback_box)
    elements.append(Spacer(1, 12))

    # 5. Source Code Submission Section
    elements.append(Paragraph("Evaluated Source Code Submission", section_title))
    raw_code = submission_data.get('code', '').strip()
    if not raw_code:
        raw_code = "# No code content submitted."

    # Format code with line numbers and safe escaping
    code_lines = raw_code.splitlines()
    formatted_code_lines = []
    for i, line in enumerate(code_lines, 1):
        clean_line = line.replace('\t', '    ')
        # Limit very long single lines to prevent overflow
        if len(clean_line) > 90:
            clean_line = clean_line[:90] + '...'
        formatted_code_lines.append(f"{i:3d} | {clean_line}")

    formatted_code_text = "\n".join(formatted_code_lines)
    pre_block = Preformatted(formatted_code_text, code_style)

    code_table = Table([[pre_block]], colWidths=[532])
    code_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), code_bg),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(code_table)

    # 6. Verification Footer
    elements.append(Spacer(1, 14))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=4, spaceAfter=6))
    footer_text = "Verified by CodeVision AI Sandbox Engine &bull; Compliant with Academic Scoring Standards"
    elements.append(Paragraph(footer_text, subtitle_style))

    doc.build(elements)

def _generate_pure_pdf(filepath, submission_data, user_data, assignment_data, evaluation_data):
    """
    Self-contained pure-Python valid PDF-1.4 binary generator.
    Creates a valid binary PDF document without relying on external packages.
    """
    student_name = user_data.get('username', 'Student')
    student_email = user_data.get('email', 'N/A')
    assign_title = assignment_data.get('title', 'Sandbox IDE Submission') if assignment_data else 'Sandbox IDE Submission'
    language = str(submission_data.get('language', 'PYTHON')).upper()
    sub_id = submission_data.get('id', 0)
    score = submission_data.get('score', 0)
    correctness = submission_data.get('correctness_score', 0)
    style = submission_data.get('style_score', 0)
    exec_time = submission_data.get('execution_time', 0.0)
    memory_mb = submission_data.get('memory_usage', 0.0)
    ai_prob = submission_data.get('ai_probability_score', 0.0)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Safe sanitization for PDF literal strings (escape parenthesis and backslashes)
    def clean_pdf_str(s):
        s = str(s).encode('latin-1', 'replace').decode('latin-1')
        return s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    lines_to_draw = [
        ("F2", 18, 50, 740, "CodeVision AI - Evaluation Report"),
        ("F1", 10, 50, 722, f"Submission Benchmark Report | Generated: {date_str}"),
        ("F2", 11, 50, 680, f"Student: {clean_pdf_str(student_name)} ({clean_pdf_str(student_email)})"),
        ("F1", 10, 50, 665, f"Assignment: {clean_pdf_str(assign_title)}"),
        ("F1", 10, 50, 650, f"Submission ID: #{sub_id}  |  Language: {clean_pdf_str(language)}"),
        ("F2", 12, 50, 615, f"Overall Score: {score} / 100"),
        ("F1", 10, 50, 595, f"Correctness Score: {correctness} / 100   |   Style Score: {style} / 100"),
        ("F1", 10, 50, 580, f"Execution Time: {exec_time}s   |   Memory: {memory_mb}MB   |   AI Probability: {ai_prob}%"),
        ("F2", 11, 50, 545, "Submitted Source Code:"),
    ]

    # Add code lines
    raw_code = submission_data.get('code', '')
    code_lines = raw_code.splitlines()[:35]  # fit first 35 lines on page
    y_pos = 525
    for i, line in enumerate(code_lines, 1):
        clean_l = clean_pdf_str(line.replace('\t', '    ')[:75])
        lines_to_draw.append(("F3", 9, 50, y_pos, f"{i:2d} | {clean_l}"))
        y_pos -= 12
        if y_pos < 60:
            break

    # Build PDF Content Stream
    stream_parts = []
    # Background decorations (lines and boxes)
    stream_parts.append("0.31 0.27 0.90 rg 50 710 512 2 re f")  # Top indigo bar
    stream_parts.append("0.95 0.96 0.98 rg 45 635 522 65 re f")  # Meta box
    stream_parts.append("0.8 0.85 0.90 RG 0.5 w 45 635 522 65 re S")
    stream_parts.append("0.94 0.96 0.99 rg 45 565 522 55 re f")  # Metrics box
    stream_parts.append("0.8 0.85 0.90 RG 0.5 w 45 565 522 55 re S")

    # Text rendering
    for font_id, size, x, y, text in lines_to_draw:
        stream_parts.append(f"BT /{font_id} {size} Tf {x} {y} Td 0 g ({text}) Tj ET")

    stream_data = "\n".join(stream_parts).encode('latin-1')
    stream_len = len(stream_data)

    # Construct complete PDF objects
    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n")
    
    offsets = []
    def add_object(obj_bytes):
        offsets.append(len(pdf))
        pdf.extend(obj_bytes)
        pdf.extend(b"\n")

    # 1: Catalog
    add_object(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    # 2: Pages
    add_object(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")
    # 3: Page
    add_object(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R /F3 7 0 R >> >> >>\nendobj")
    # 4: Contents Stream
    add_object(f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode('latin-1') + stream_data + b"\nendstream\nendobj")
    # 5: Font F1 (Helvetica)
    add_object(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")
    # 6: Font F2 (Helvetica-Bold)
    add_object(b"6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj")
    # 7: Font F3 (Courier)
    add_object(b"7 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj")

    # XRef Table
    xref_offset = len(pdf)
    num_objects = len(offsets) + 1
    pdf.extend(f"xref\n0 {num_objects}\n0000000000 65535 f \n".encode('latin-1'))
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode('latin-1'))
    
    # Trailer
    pdf.extend(f"trailer\n<< /Size {num_objects} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode('latin-1'))

    with open(filepath, 'wb') as f:
        f.write(pdf)

def generate_csv_export(submissions_list):
    """
    Exports submission records as CSV string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Submission ID", "Student Username", "Assignment Title", "Language",
        "Overall Score", "Correctness Score", "Style Score", "Execution Time (s)",
        "Memory (MB)", "AI Probability (%)", "Submitted At"
    ])

    for sub in submissions_list:
        writer.writerow([
            sub.get('id'),
            sub.get('username', 'N/A'),
            sub.get('assignment_title', 'N/A'),
            sub.get('language'),
            sub.get('score'),
            sub.get('correctness_score'),
            sub.get('style_score'),
            sub.get('execution_time'),
            sub.get('memory_usage'),
            sub.get('ai_probability_score'),
            sub.get('created_at')
        ])

    return output.getvalue()

