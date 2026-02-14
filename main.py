from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import fitz  # PyMuPDF
import requests
import os
from openai import OpenAI
import json

app = FastAPI()

# Initialize OpenAI client (make sure your key is set in environment variables)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PdfUrlRequest(BaseModel):
    pdfUrl: str

def extract_text_from_pdf_pages(pdf_bytes):
    """Extract text page by page and return as a list of dicts with page number."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            if text:  # Only include pages with text
                pages.append({"page": page_number, "text": text})
        return pages
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF read error: {e}")

@app.post("/upload-pdf-url/")
async def upload_pdf_url(data: PdfUrlRequest):
    try:
        # Download PDF
        resp = requests.get(data.pdfUrl)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download PDF")

        pdf_bytes = resp.content
        pages = extract_text_from_pdf_pages(pdf_bytes)

        if not pages:
            raise HTTPException(status_code=400, detail="PDF has no extractable text")

        all_mcqs = []

        for page in pages:
            prompt = f"""
            Create multiple choice questions from the following page content.
            Return **strict JSON array** with keys:
            question (string), options (list of 4 strings), answer_index (0-3), explanation (string)

            Content (Page {page['page']}):
            {page['text'][:3000]}  # Limit to 3000 chars to avoid token limits
            """

            # Call OpenAI
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )

            ai_output = response.choices[0].message.content.strip()

            # Parse AI JSON safely
            try:
                mcqs = json.loads(ai_output)
                if isinstance(mcqs, list):
                    # Add page number to each question
                    for mcq in mcqs:
                        mcq["page_number"] = page["page"]
                    all_mcqs.extend(mcqs)
            except json.JSONDecodeError:
                # Skip pages with invalid JSON output
                continue

        if not all_mcqs:
            raise HTTPException(status_code=500, detail="AI did not return any questions")

        return {"mcqs": all_mcqs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
