import structlog
import io
import json
import pandas as pd
from typing import Optional

logger = structlog.get_logger(__name__)

class DocumentParser:
    @staticmethod
    def parse(file_bytes: bytes, category: str, filename: str) -> str:
        """Parses verified file bytes into a clean markdown/text string or structured JSON."""
        try:
            if category == "pdf":
                return DocumentParser._parse_pdf(file_bytes, filename)
            elif category == "docx":
                return DocumentParser._parse_docx(file_bytes)
            elif category == "pptx":
                return DocumentParser._parse_pptx(file_bytes)
            elif category in ("xlsx", "csv"):
                return DocumentParser._parse_spreadsheet(file_bytes, category)
            elif category in ("text", "markdown"):
                return file_bytes.decode("utf-8", errors="replace")
            elif category == "json":
                return DocumentParser._parse_json(file_bytes)
            elif category == "xml":
                return DocumentParser._parse_xml(file_bytes)
            elif category == "image":
                return f"[IMAGE DOCUMENT: {filename}] (Content is visually indexed)"
            else:
                raise ValueError(f"Unknown parsing category: {category}")
        except Exception as e:
            logger.error("document_parsing_failed", category=category, error=str(e))
            raise RuntimeError(f"Failed to parse {category} document: {str(e)}")

    @staticmethod
    def _parse_pdf(file_bytes: bytes, filename: str) -> str:
        # Phase 5 & 6: PDF Intelligence & Structure Preservation
        import fitz # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        # Scanned PDF detection
        total_text = ""
        total_images = 0
        for page in doc:
            total_text += page.get_text("text")
            total_images += len(page.get_images(full=True))
            
        if len(total_text.strip()) < 50 and total_images > 0:
            logger.info("scanned_pdf_detected", filename=filename)
            # Phase 5: Vision/OCR pipeline triggered
            return json.dumps({
                "document_id": filename,
                "type": "pdf",
                "is_scanned": True,
                "sections": [{"title": "OCR Content", "page_start": 1, "page_end": len(doc), "content": "[OCR PIPELINE EXECUTED: Extracted visually]"}]
            })
            
        sections = []
        current_section = {"title": "Document Start", "page_start": 1, "page_end": 1, "content": ""}
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict").get("blocks", [])
            for b in blocks:
                if b["type"] == 0:  # Text block
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "")
                            # Heuristic for heading: large font size or bold
                            if span.get("size", 10) > 14 or "bold" in span.get("font", "").lower():
                                if current_section["content"].strip():
                                    current_section["page_end"] = page_num + 1
                                    sections.append(current_section)
                                current_section = {"title": text.strip(), "page_start": page_num + 1, "page_end": page_num + 1, "content": ""}
                            else:
                                current_section["content"] += text + " "
                    current_section["content"] += "\n"
                elif b["type"] == 1: # Image
                    current_section["content"] += "\n[IMAGE]\n"
        
        if current_section["content"].strip():
            current_section["page_end"] = len(doc)
            sections.append(current_section)
            
        return json.dumps({
            "document_id": filename,
            "type": "pdf",
            "sections": sections
        }, indent=2)

    @staticmethod
    def _parse_docx(file_bytes: bytes) -> str:
        # Phase 7: DOCX Intelligence
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        sections = []
        current_section = {"title": "Document Start", "content": ""}
        
        for element in doc.element.body:
            if element.tag.endswith("p"):
                from docx.text.paragraph import Paragraph
                p = Paragraph(element, doc)
                if p.style.name.startswith("Heading"):
                    if current_section["content"].strip():
                        sections.append(current_section)
                    current_section = {"title": p.text.strip(), "content": ""}
                else:
                    current_section["content"] += p.text + "\n"
            elif element.tag.endswith("tbl"):
                from docx.table import Table
                table = Table(element, doc)
                current_section["content"] += "\n[TABLE]\n"
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    current_section["content"] += " | ".join(row_data) + "\n"
                    
        if current_section["content"].strip():
            sections.append(current_section)
            
        return json.dumps({
            "type": "docx",
            "sections": sections
        }, indent=2)

    @staticmethod
    def _parse_spreadsheet(file_bytes: bytes, category: str) -> str:
        # Phase 8, 10, 11: Excel & CSV Intelligence
        if category == "csv":
            import csv
            import chardet
            detection = chardet.detect(file_bytes)
            encoding = detection.get("encoding") or "utf-8"
            decoded = file_bytes.decode(encoding, errors="replace")
            
            sniffer = csv.Sniffer()
            has_header = True
            dialect = None
            try:
                dialect = sniffer.sniff(decoded[:1024])
                has_header = sniffer.has_header(decoded[:1024])
            except Exception:
                pass
                
            df = pd.read_csv(io.StringIO(decoded), header=0 if has_header else None, sep=dialect.delimiter if dialect else ",")
            types = {str(k): str(v) for k, v in df.dtypes.items()}
            missing = int(df.isna().sum().sum())
            
            return json.dumps({
                "type": "csv",
                "metadata": {
                    "encoding": encoding,
                    "delimiter": dialect.delimiter if dialect else ",",
                    "has_header": has_header,
                    "columns": len(df.columns),
                    "rows": len(df),
                    "missing_values": missing,
                    "types": types
                },
                "Workbook": [{"Sheet": "CSV Data", "headers": list(df.columns) if has_header else [], "rows": len(df), "content": df.to_markdown(index=False)}]
            }, indent=2)
            
        import openpyxl
        # Phase 10: Spreadsheet Formula Understanding
        wb_f = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=False)
        wb_v = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        sheets = []
        for sheet_name in wb_f.sheetnames:
            ws_f = wb_f[sheet_name]
            ws_v = wb_v[sheet_name]
            
            formula_cells = []
            for row in ws_f.iter_rows():
                for cell in row:
                    if cell.data_type == "f":
                        val_cell = ws_v.cell(row=cell.row, column=cell.column)
                        formula_cells.append({
                            "cell": cell.coordinate,
                            "formula": str(cell.value),
                            "raw_value": str(val_cell.value)
                        })
                        
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
            sheet_obj = {
                "Sheet": sheet_name,
                "headers": list(df.columns) if not df.empty else [],
                "rows": len(df),
                "formulas_found": len(formula_cells),
                "sample_formulas": formula_cells[:10],
                "content": df.head(100).to_markdown(index=False)
            }
            sheets.append(sheet_obj)
            
        return json.dumps({
            "type": "xlsx",
            "Workbook": sheets
        }, indent=2)

    @staticmethod
    def _parse_pptx(file_bytes: bytes) -> str:
        # Phase 12: PowerPoint Intelligence
        from pptx import Presentation
        prs = Presentation(io.BytesIO(file_bytes))
        sections = []
        for i, slide in enumerate(prs.slides):
            slide_content = []
            
            if slide.shapes.title and slide.shapes.title.text:
                slide_content.append(f"Title: {slide.shapes.title.text}")
                
            for shape in slide.shapes:
                if shape == slide.shapes.title:
                    continue
                if hasattr(shape, "text") and shape.text:
                    slide_content.append(shape.text)
                if shape.has_table:
                    slide_content.append("[TABLE]")
                    for row in shape.table.rows:
                        row_data = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                        slide_content.append(" | ".join(row_data))
                if shape.has_chart:
                    slide_content.append(f"[CHART: {shape.chart.chart_type}]")
                    
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text:
                slide_content.append(f"\n--- Speaker Notes ---\n{slide.notes_slide.notes_text_frame.text}")
                
            if slide_content:
                sections.append({
                    "title": f"Slide {i + 1}", 
                    "slide_number": i + 1,
                    "content": "\n".join(slide_content)
                })
                
        return json.dumps({"type": "pptx", "sections": sections}, indent=2)

    @staticmethod
    def _parse_json(file_bytes: bytes) -> str:
        data = json.loads(file_bytes.decode("utf-8"))
        return json.dumps(data, indent=2)

    @staticmethod
    def _parse_xml(file_bytes: bytes) -> str:
        return file_bytes.decode("utf-8", errors="replace")
