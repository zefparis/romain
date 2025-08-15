from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from docxtpl import DocxTemplate
import io, pandas as pd
router = APIRouter()
env = Environment(loader=FileSystemLoader("templates"))
@router.post("/export/pdf")
def export_pdf(body: dict):
    tpl = env.get_template(body.get("template", "report.html"))
    html = tpl.render(**body.get("data", {}))
    pdf = HTML(string=html).write_pdf()
    return Response(pdf, media_type="application/pdf")
@router.post("/export/docx")
def export_docx(body: dict):
    tpl = DocxTemplate("templates/report.docx")
    tpl.render(body.get("data", {}))
    buf = io.BytesIO(); tpl.save(buf); buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
@router.post("/export/xlsx")
def export_xlsx(body: dict):
    rows = body.get("data", {}).get("rows", [])
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df.to_excel(w, index=False, sheet_name="Feuille1")
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
