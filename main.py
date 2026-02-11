from fastapi import FastAPI, HTTPException, Query
import fitz
import httpx
import os
from openai import OpenAI

app = FastAPI()

# Load OpenAI key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF read error: {e}")

@app.post("/upload-pdf-url/")
async def upload_pdf_url(pdfUrl: str = Query(...)):
    try:
        # Download PDF
        async with httpx.AsyncClient(timeout=60.0) as client_http:
            resp = await client_http.get(pdfUrl)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to download PDF")
            pdf_bytes = resp.content

        text = extract_text_from_pdf(pdf_bytes)

        if len(text) < 50:
            raise HTTPException(status_code=400, detail="PDF text too short")

        # 🔥 AI PROMPT
        prompt = f"""
        You are an expert exam question generator.

        Generate 10 high quality MCQs from the following text.

        Rules:
        - Each MCQ must contain:
          topic
          question
          options (4)
          correctIndex (0-3)
          explanation
          difficulty (easy/medium/hard)
          language (en)
          mode (theory)

        Return strictly valid JSON array only.

        Text:
        {text[:5000]}
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
