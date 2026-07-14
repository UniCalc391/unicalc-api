from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

app = FastAPI()

# 1. ОБЯЗАТЕЛЬНО: Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AIRequest(BaseModel):
    prompt: str

# Ключ из переменных окружения Render
GEMINI_KEY = os.environ.get("GEMINI_KEY", "ТВОЙ_РЕАЛЬНЫЙ_КЛЮЧ")

@app.post("/api/analyze")
def analyze_text(req: AIRequest):
    # Используем стабильную модель 1.5 flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    # ЖЕСТКИЙ ФИЛЬТР ИИ: Задаем личность элитного ментора на уровне сервера
    system_instruction = (
        "Ты — элитный, дорогой ментор по поступлению в топовые вузы мира (Bocconi, Ivy League). "
        "Твой стиль общения: дерзкий, уверенный, профессиональный, без канцелярщины и воды. "
        "Ты говоришь правду прямо в лицо. Если видишь слабое место — указывай на него жестко, но давай прагматичный план исправления. "
        "ТЕБЕ СТРОГО ЗАПРЕЩЕНО использовать ИИ-шаблоны: 'в заключение', 'важно отметить', 'как ИИ-модель', 'я рекомендую'. "
        "Общайся как живой человек. Выдавай ответ СТРОГО в том формате JSON, который указан в запросе пользователя."
    )

    # Формируем безопасный payload
    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {"parts": [{"text": req.prompt}]}
        ]
    }
    
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    return response.json()