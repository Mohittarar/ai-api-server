from fastapi import FastAPI, HTTPException, Query
import fitz  # PyMuPDF
import httpx  # Async HTTP client

app = FastAPI()

# ---------------- PDF TEXT EXTRACTION ----------------
def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF read error: {e}")

# ---------------- HEALTH CHECK ----------------
@app.get("/")
def home():
    return {"message": "FastAPI server running on Render"}

# ---------------- UPLOAD PDF VIA URL ----------------
@app.post("/upload-pdf-url/")
async def upload_pdf_url(pdfUrl: str = Query(..., description="Public URL of PDF file")):
    """
    Download PDF from a URL, extract text, and return a simple MCQ.
    """
    try:
        # Async download with timeout
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(pdfUrl)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to download PDF from URL")
            pdf_bytes = resp.content

        # Limit PDF size (optional)
        if len(pdf_bytes) > 10 * 1024 * 1024:  # 10 MB limit
            raise HTTPException(status_code=413, detail="PDF too large (max 10MB)")

        # Extract text
        text = extract_text_from_pdf(pdf_bytes)

        # Prepare simple MCQs
        first_word = text.split(" ")[0] if text else ""
        mcqs = [
            {
                "question": "PDF ka first word kya hai?",
                "options": ["A", "B", "C", first_word],
                "answer": first_word
            }
        ]

        return {
            "filename": "from_url.pdf",
            "text_length": len(text),
            "mcqs": mcqs
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}")
