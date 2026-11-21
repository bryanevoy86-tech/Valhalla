"""Bounded subprocess parser. Its only input is a declared MIME type and file bytes."""
from io import BytesIO
import json
import re
import resource
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile


MAX_INPUT = 5 * 1024 * 1024
MAX_XML = 2 * 1024 * 1024
MAX_SECTIONS = 20
MAX_CHARS = 2000
WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SHEET_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def bounded(sections, kind, **details):
    trimmed = len(sections) > MAX_SECTIONS or any(len(text) > MAX_CHARS for _, text in sections)
    return {
        "format": kind,
        "sections": [{"locator": ref, "text": text[:MAX_CHARS]} for ref, text in sections[:MAX_SECTIONS]],
        "bounded_output": trimmed,
        **details,
    }


def xml_entry(archive, name):
    info = archive.getinfo(name)
    if info.file_size > MAX_XML:
        raise ValueError("XML member too large")
    data = archive.read(info).decode("utf-8-sig")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", data, flags=re.I):
        raise ValueError("XML declarations not allowed")
    return ET.fromstring(data)


def office(data, mime):
    with ZipFile(BytesIO(data)) as archive:
        infos = archive.infolist()
        if len(infos) > 128 or sum(item.file_size for item in infos) > 32 * 1024 * 1024:
            raise ValueError("office container too large")
        names = {item.filename for item in infos}
        if len(names) != len(infos):
            raise ValueError("duplicate office member")
        if mime.endswith("wordprocessingml.document"):
            root = xml_entry(archive, "word/document.xml")
            paragraphs = root.findall(f".//{WORD_NS}p")
            sections = [(f"paragraph {i}", 
                         "".join(node.text or "" for node in p.iter(f"{WORD_NS}t")))
                        for i, p in enumerate(paragraphs[:MAX_SECTIONS + 1], 1)]
            return bounded(sections, "DOCX", paragraph_count=len(paragraphs))
        sheet_names = sorted(name for name in names if re.fullmatch(r"xl/worksheets/sheet[0-9]+\.xml", name))
        if not sheet_names:
            raise ValueError("workbook lacks worksheet")
        shared = []
        if "xl/sharedStrings.xml" in names:
            strings = xml_entry(archive, "xl/sharedStrings.xml")
            shared = ["".join(node.text or "" for node in item.iter(f"{SHEET_NS}t"))
                      for item in strings.findall(f"{SHEET_NS}si")]
        sections = []
        for name in sheet_names[:MAX_SECTIONS + 1]:
            root = xml_entry(archive, name)
            values = []
            for cell in root.iter(f"{SHEET_NS}c"):
                ref = cell.get("r", "")
                if not re.fullmatch(r"[A-Z]{1,3}[1-9][0-9]{0,6}", ref):
                    continue
                if cell.find(f"{SHEET_NS}f") is not None:
                    value = "[formula omitted]"
                elif cell.get("t") == "inlineStr":
                    value = "".join(t.text or "" for t in cell.iter(f"{SHEET_NS}t"))
                else:
                    value = cell.findtext(f"{SHEET_NS}v", "")
                    if cell.get("t") == "s":
                        if not value.isascii() or not value.isdigit() or len(value) > 8 or int(value) >= len(shared):
                            raise ValueError("invalid shared-string reference")
                        value = shared[int(value)]
                values.append(f"{ref}\t{value[:MAX_CHARS]}")
                if sum(map(len, values)) >= MAX_CHARS or len(values) > 100:
                    break
            sections.append((name, "\n".join(values)))
        return bounded(sections, "XLSX", worksheet_count=len(sheet_names), formulas_evaluated=False)


def parse(data, mime):
    if mime == "text/plain":
        return bounded([("text", data.decode("utf-8"))], "TEXT")
    if mime.startswith("application/vnd.openxmlformats-officedocument."):
        return office(data, mime)
    if mime == "application/pdf":
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise ValueError("encrypted PDFs are unsupported")
        count = len(reader.pages)
        sections = [(f"page {i + 1}", reader.pages[i].extract_text() or "")
                    for i in range(min(count, MAX_SECTIONS))]
        result = bounded(sections, "PDF", page_count=count, ocr_performed=False)
        result["bounded_output"] |= count > MAX_SECTIONS
        return result
    if mime in {"image/png", "image/jpeg"}:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = 12_000_000
        with Image.open(BytesIO(data), formats=["PNG"] if mime == "image/png" else ["JPEG"]) as image:
            if image.width * image.height > Image.MAX_IMAGE_PIXELS:
                raise ValueError("image pixel limit exceeded")
            result = bounded([], image.format, width=image.width, height=image.height, vision_performed=False)
            image.verify()
            return result
    raise ValueError("unsupported media type")


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (4, 5))
    resource.setrlimit(resource.RLIMIT_AS, (384 * 1024 * 1024, 384 * 1024 * 1024))
    data = sys.stdin.buffer.read(MAX_INPUT + 1)
    if not 0 < len(data) <= MAX_INPUT:
        return 2
    try:
        print(json.dumps(parse(data, sys.argv[1])))
    except Exception:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
