from fastapi import FastAPI, File, UploadFile
import fitz  # PyMuPDF

app = FastAPI()

@app.get("/")
def home():
    return {"message": "FastAPI server running on Render"}

def extract_text_from_pdf(pdf_bytes):
    text = ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        text += page.get_text()
    return text

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    text = extract_text_from_pdf(pdf_bytes)

    # simple demo MCQ
    mcqs = [
        {
            "question": "PDF ka first word kya hai?",
            "options": ["A", "B", "C", text.split(" ")[0]],
            "answer": text.split(" ")[0]
        }
    ]

    return {
        "filename": file.filename,
        "text_length": len(text),
        "mcqs": mcqs
    }
