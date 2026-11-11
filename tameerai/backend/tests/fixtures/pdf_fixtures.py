"""
TameerAI - Synthetic PDF Fixture Generators (Phase 03B)
Creates deterministic, in-memory synthetic PDF documents for testing:
1. Normal one-page text PDF
2. Multi-page text PDF
3. Scanned/image-based PDF (raster image, 0 native text)
4. Mixed native/scanned PDF
5. Rotated page PDF
6. Empty page PDF
7. Malformed PDF bytes
8. Encrypted/password-protected PDF
9. Simple table PDF
10. Oversized/page-limit exceeding PDF

All fixtures are generated locally in memory. Zero access to protected regulatory files.
"""

import io
from typing import List, Optional
from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


def generate_single_page_text_pdf(
    text: str = "TameerAI Synthetic Project Specification. Concrete compressive strength 3000 PSI."
) -> bytes:
    """Generates a clean 1-page native text PDF."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(72, 720, text)
    c.drawString(72, 700, "Section 1: General Requirements and Building Standards.")
    c.save()
    return buf.getvalue()


def generate_multi_page_text_pdf(
    pages_text: Optional[List[str]] = None
) -> bytes:
    """Generates a multi-page native text PDF."""
    if pages_text is None:
        pages_text = [
            "Page 1: Architectural Site Plan and Boundary Disclosures.",
            "Page 2: Structural Column Schedule and Foundation Details.",
            "Page 3: Mechanical, Electrical, and Plumbing (MEP) Layout."
        ]
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    for idx, p_text in enumerate(pages_text):
        c.drawString(72, 720, p_text)
        c.drawString(72, 700, f"Document Sequence Turn #{idx + 1}")
        c.showPage()
    c.save()
    return buf.getvalue()


def generate_scanned_image_pdf(
    text_in_image: str = "SCANNED MUNICIPAL NOTICE - ALL SETBACKS MUST BE VERIFIED"
) -> bytes:
    """
    Generates a scanned/image-only PDF page.
    Renders text into a raster PIL Image and embeds it as a graphic.
    Zero native selectable text exists in the PDF stream.
    """
    # Create white raster canvas
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw simple lines simulating scanned document
    draw.text((50, 50), text_in_image, fill=(0, 0, 0))
    draw.text((50, 100), "Municipal Authority Building Control Department Stamp: APPROVED", fill=(0, 0, 0))
    draw.line([(50, 80), (750, 80)], fill=(128, 128, 128), width=2)

    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_buf.seek(0)

    # Embed raster image onto PDF canvas
    pdf_buf = io.BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=letter)
    from reportlab.lib.utils import ImageReader
    c.drawImage(ImageReader(img_buf), 50, 200, width=500, height=375)
    c.save()
    return pdf_buf.getvalue()


def generate_mixed_pdf() -> bytes:
    """
    Generates a 2-page PDF where:
    - Page 1 is native readable text.
    - Page 2 is a raster image with zero native text.
    """
    # Page 1: Native text
    p1_buf = io.BytesIO()
    c1 = canvas.Canvas(p1_buf, pagesize=letter)
    c1.drawString(72, 720, "Page 1: Native engineering specification and general provisions.")
    c1.drawString(72, 700, "All drawings shall be submitted in accordance with zoning bylaws.")
    c1.save()

    # Page 2: Scanned image
    p2_bytes = generate_scanned_image_pdf("PAGE 2 SCANNED DRAWING ATTACHMENT")

    # Combine using pypdf
    writer = PdfWriter()
    reader1 = PdfReader(io.BytesIO(p1_buf.getvalue()))
    reader2 = PdfReader(io.BytesIO(p2_bytes))

    writer.add_page(reader1.pages[0])
    writer.add_page(reader2.pages[0])

    out_buf = io.BytesIO()
    writer.write(out_buf)
    return out_buf.getvalue()


def generate_rotated_page_pdf(rotation: int = 90) -> bytes:
    """Generates a PDF page with explicit rotation metadata (e.g. 90 degrees)."""
    base_pdf = generate_single_page_text_pdf("Rotated engineering drawing sheet layout.")
    reader = PdfReader(io.BytesIO(base_pdf))
    writer = PdfWriter()
    page = reader.pages[0]
    page.rotate(rotation)
    writer.add_page(page)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def generate_empty_page_pdf() -> bytes:
    """Generates a blank PDF page with zero text and zero images."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def generate_malformed_pdf() -> bytes:
    """Generates corrupt, invalid PDF bytes."""
    return b"%PDF-1.4\n%CORRUPT_MALFORMED_HEADER_BYTES_RANDOM_NOISE_12345\n%%EOF"


def generate_encrypted_pdf(password: str = "secret123") -> bytes:
    """Generates a password-protected encrypted PDF."""
    base_pdf = generate_single_page_text_pdf("Confidential synthetic contract clause.")
    reader = PdfReader(io.BytesIO(base_pdf))
    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    writer.encrypt(user_password=password, owner_password=password + "_owner")

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def generate_table_pdf(
    headers: Optional[List[str]] = None,
    rows: Optional[List[List[str]]] = None
) -> bytes:
    """Generates a PDF containing a structured tabular schedule (e.g. BOQ schedule)."""
    if headers is None:
        headers = ["Item No.", "Description", "Unit", "Quantity", "Unit Rate (PKR)"]
    if rows is None:
        rows = [
            ["1.01", "Excavation in all types of soil", "Cu.Ft", "15,000", "45.00"],
            ["1.02", "Plain Cement Concrete (1:4:8)", "Cu.Ft", "3,500", "280.00"],
            ["1.03", "Reinforced Cement Concrete (1:2:4)", "Cu.Ft", "8,200", "520.00"],
        ]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("<b>Synthetic Bill of Quantities Schedule</b>", styles["Title"]))
    elements.append(Spacer(1, 14))

    table_data = [headers] + rows
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(t)
    doc.build(elements)
    return buf.getvalue()


def generate_oversized_page_count_pdf(num_pages: int = 105) -> bytes:
    """Generates a synthetic PDF with page count exceeding the safety limit (100)."""
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()

