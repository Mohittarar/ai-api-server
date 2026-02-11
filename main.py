from fastapi import FastAPI, File, UploadFile, HTTPException
import fitz  # PyMuPDF

app = FastAPI()

@app.get("/")
def home():
    return {"message": "FastAPI server running on Render"}

def extract_text_from_pdf(pdf_bytes):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF read error: {e}")

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=422, detail="File must be a PDF")

        pdf_bytes = await file.read()
        if len(pdf_bytes) > 5 * 1024 * 1024:  # limit 5MB for Render free plan
            raise HTTPException(status_code=413, detail="PDF too large (max 5MB)")

        text = extract_text_from_pdf(pdf_bytes)

        # Simple MCQ demo
        mcqs = [
            {
                "question": "PDF ka first word kya hai?",
                "options": ["A", "B", "C", text.split(" ")[0] if text else ""],
                "answer": text.split(" ")[0] if text else ""
            }
        ]

        return {"filename": file.filename, "text_length": len(text), "mcqs": mcqs}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}")
