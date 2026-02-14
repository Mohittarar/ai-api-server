from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import fitz
import requests
import os
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.getenv("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"))

class PdfUrlRequest(BaseModel):
    pdfUrl: str

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
async def upload_pdf_url(data: PdfUrlRequest):
    try:
        resp = requests.get(data.pdfUrl)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download PDF")

        pdf_bytes = resp.content
        text = extract_text_from_pdf(pdf_bytes)

        if not text.strip():
            raise HTTPException(status_code=400, detail="Empty PDF content")

        # 🔥 OpenAI Call
        prompt = f"""
        Create 10 multiple choice questions from the following content.
        Return JSON array format:
        [
          {{
            "question": "...",
            "options": ["A","B","C","D"],
            "answer_index": 0,
            "explanation": "..."
          }}
        ]

        Content:
        {text[:4000]}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        ai_output = response.choices[0].message.content

        return {"mcqs": ai_output}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
