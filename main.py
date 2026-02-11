from fastapi import FastAPI, HTTPException
import fitz
import requests

app = FastAPI()

def extract_text_from_pdf(pdf_bytes):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF read error: {e}")

@app.post("/upload-pdf-url/")
async def upload_pdf_url(pdfUrl: str):
    try:
        resp = requests.get(pdfUrl)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download PDF")
        pdf_bytes = resp.content
        if len(pdf_bytes) > 20 * 1024 * 1024:  # optional: 20MB limit
            raise HTTPException(status_code=413, detail="PDF too large")

        text = extract_text_from_pdf(pdf_bytes)
        mcqs = [
            {
                "question": "PDF ka first word kya hai?",
                "options": ["A", "B", "C", text.split(" ")[0] if text else ""],
                "answer": text.split(" ")[0] if text else ""
            }
        ]

        return {"filename": "from_url.pdf", "text_length": len(text), "mcqs": mcqs}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}")
