# -*- coding: utf-8 -*-
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse, Response, FileResponse
from jinja2 import Environment, FileSystemLoader
import io, pandas as pd
import os

# WeasyPrint en option (Windows peut manquer de libs GTK/Pango/Cairo)
HAS_WEASY = False
try:
    from weasyprint import HTML  # type: ignore
    HAS_WEASY = True
except Exception:
    HAS_WEASY = False

router = APIRouter()
env = Environment(loader=FileSystemLoader("templates"))
UPLOAD_DIR = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/export/pdf")
def export_pdf(body: dict):
    data = body.get("data", {})
    # Si WeasyPrint dispo => HTML->PDF
    if HAS_WEASY:
        tpl_name = body.get("template", "report.html")
        tpl = env.get_template(tpl_name)
        html = tpl.render(**data)
        pdf = HTML(string=html).write_pdf()
        return Response(pdf, media_type="application/pdf")

    # Fallback ReportLab: prend data.text (texte brut), sinon un message par défaut
    from reportlab.pdfgen import canvas  # lazy import
    from reportlab.lib.pagesizes import A4
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 50

    text = data.get("text") or (
        "WeasyPrint indisponible sur Windows (GTK/Pango/Cairo manquants).\n"
        "Fallback ReportLab actif. Fournissez data.text pour un rendu texte.\n"
        "Exemple payload: {\"format\":\"pdf\",\"data\":{\"text\":\"Bonjour Romain\"}}"
    )

    for line in str(text).splitlines():
        c.drawString(50, y, line[:110])  # coupe un peu pour éviter d'aller hors page
        y -= 16
        if y < 50:
            c.showPage(); y = height - 50
    c.save()
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf")

@router.post("/export/docx")
def export_docx(body: dict):
    from docxtpl import DocxTemplate
    tpl = DocxTemplate("templates/report.docx")
    tpl.render(body.get("data", {}))
    stream = io.BytesIO(); tpl.save(stream); stream.seek(0)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@router.post("/export/xlsx")
def export_xlsx(body: dict):
    rows = body.get("data", {}).get("rows", [])
    df = pd.DataFrame(rows)
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine="xlsxwriter") as w:
        df.to_excel(w, index=False, sheet_name="Feuille1")
    stream.seek(0)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    saved = []
    for f in files:
        dest = os.path.join(UPLOAD_DIR, f.filename)
        with open(dest, "wb") as out:
            content = await f.read()
            out.write(content)
        saved.append({"name": f.filename, "size": len(content)})
    return {"files": saved}

@router.get("/files")
def list_files():
    items = []
    for name in sorted(os.listdir(UPLOAD_DIR)):
        path = os.path.join(UPLOAD_DIR, name)
        if os.path.isfile(path):
            items.append({"name": name, "size": os.path.getsize(path)})
    return {"files": items}

@router.get("/files/{name}")
def get_file(name: str):
    path = os.path.join(UPLOAD_DIR, name)
    if not os.path.isfile(path):
        return Response(status_code=404)
    return FileResponse(path, filename=name)
