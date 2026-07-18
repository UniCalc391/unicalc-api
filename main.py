from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
import requests
from bs4 import BeautifulSoup

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка Gemini
# Используй переменную окружения, как мы обсуждали
api_key = os.getenv("GEMINI_API_KEY") 
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

class RequestBody(BaseModel):
    prompt: str = None
    url: str = None

@app.post("/api/analyze")
async def analyze(body: RequestBody):
    try:
        response = model.generate_content(body.prompt)
        return {"candidates": [{"content": {"parts": [{"text": response.text}]}}]}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/parse-program")
async def parse_program(body: RequestBody):
    try:
        # 1. Скачиваем содержимое сайта
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(body.url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Убираем скрипты и стили для чистого текста
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=' ', strip=True)
        
        # Берем только первые 10000 символов, чтобы не перегрузить Gemini
        clean_text = text[:10000]

        # 2. Просим Gemini вытащить инсайты
        prompt = f"Вытащи из этого текста программы вуза ключевые дисциплины, требования, имена профессоров и уникальные фишки. Оформи в виде структурированного списка:\n\n{clean_text}"
        response = model.generate_content(prompt)
        
        return {"insights": response.text}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    return {"message": "UniCalc API is alive!"}