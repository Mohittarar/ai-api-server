from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import fitz  # PyMuPDF
import requests
import os
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.getenv("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"))

class PdfUrlRequest(BaseModel):
    pdfUrl: str

def extract_text_from_pdf_pages(pdf_bytes):
    """Extract text **page by page** and return as a list of strings."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text()
            if text.strip():
                pages.append({"page": page_number, "text": text})
        return pages
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF read error: {e}")

@app.post("/upload-pdf-url/")
async def upload_pdf_url(data: PdfUrlRequest):
    try:
        resp = requests.get(data.pdfUrl)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download PDF")

        pdf_bytes = resp.content
        pages = extract_text_from_pdf_pages(pdf_bytes)

        if not pages:
            raise HTTPException(status_code=400, detail="Empty PDF content")

        all_mcqs = []

        for page in pages:
            prompt = f"""
            Create multiple choice questions from the following page content.
            Return JSON array format with keys:
            question, options (A-D), answer_index (0-3), explanation, page_number

            Content:
            {page['text'][:3000]}
            """
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )

            ai_output = response.choices[0].message.content

            # Optional: parse AI JSON safely
            import json
            try:
                mcqs = json.loads(ai_output)
                # Add page info if not included
                for mcq in mcqs:
                    mcq["page_number"] = page["page"]
                all_mcqs.extend(mcqs)
            except json.JSONDecodeError:
                # If AI returns invalid JSON
                continue

        return {"mcqs": all_mcqs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
