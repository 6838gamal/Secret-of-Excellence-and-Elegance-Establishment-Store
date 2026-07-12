"""Invoice PDF generator using ReportLab."""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode as qr_lib
import os
from app.config.settings import settings


def generate_invoice_pdf(order, payment_link, service=None) -> bytes:
    """Generate a PDF invoice and return it as bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1a1a2e"),
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    story.append(Paragraph(settings.COMPANY_NAME, title_style))
    story.append(Paragraph("فاتورة / Invoice", title_style))
    story.append(Spacer(1, 0.5 * cm))

    # Invoice details table
    data = [
        ["رقم الفاتورة:", f"INV-{order.id:06d}"],
        ["رقم العملية UUID:", str(order.uuid)],
        ["العميل:", order.customer_name or "—"],
        ["البريد الإلكتروني:", order.customer_email or "—"],
        ["الهاتف:", order.customer_phone or "—"],
        ["الخدمة:", service.title if service else (payment_link.description or "—")],
        ["المبلغ:", f"{order.amount:.2f} {order.currency}"],
        ["حالة الدفع:", order.status.value],
        ["رقم المعاملة:", order.transaction_id or "—"],
    ]

    table = Table(data, colWidths=[5 * cm, 12 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1a1a2e")),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 1 * cm))

    # QR Code
    base_url = os.environ.get("REPLIT_DEV_DOMAIN", "http://localhost:5000")
    qr_data = f"https://{base_url}/invoice/{order.id}"
    qr_img = qr_lib.make(qr_data)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    story.append(Image(qr_buffer, width=4 * cm, height=4 * cm))

    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceBefore=10,
    )
    story.append(Paragraph("شكرًا لتعاملكم معنا — مؤسسة سر التميز والأناقة", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
