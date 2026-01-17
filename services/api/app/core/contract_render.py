"""
Render helper for contracts: Jinja2 template -> text -> PDF (via ReportLab).
"""

import io
from typing import Dict, Any
from jinja2 import Environment, BaseLoader
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


def render_text(template_str: str, data: Dict[str, Any]) -> str:
    env = Environment(loader=BaseLoader(), autoescape=False, trim_blocks=True, lstrip_blocks=True)
    tmpl = env.from_string(template_str)
    return tmpl.render(**data)


def make_pdf(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    width, height = LETTER
    x, y = 0.75 * inch, height - 0.75 * inch
    c.setFont("Helvetica", 10)
    # simple word-wrap
    for para in text.split("\n"):
        line = para
        while len(line) > 0:
            # ~90 chars per line approximate; tweak if needed
            chunk = line[:90]
            c.drawString(x, y, chunk)
            y -= 14
            line = line[90:]
            if y < 0.75 * inch:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - 0.75 * inch
        y -= 6
        if y < 0.75 * inch:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 0.75 * inch
    c.showPage()
    c.save()
    return buf.getvalue()
