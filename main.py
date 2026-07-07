from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

app = FastAPI()

# 1. ОБЯЗАТЕЛЬНО: Настройка CORS (разрешает твоему сайту слать сюда запросы)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Формат данных от сайта
class AIRequest(BaseModel):
    prompt: str

# 3. Ключ из переменных окружения Render
GEMINI_KEY = os.environ.get("GEMINI_KEY", "ТВОЙ_РЕАЛЬНЫЙ_КЛЮЧ")

# 4. ТОТ САМЫЙ МАРШРУТ, который сейчас выдает 404
@app.post("/api/analyze")
def analyze_text(req: AIRequest):
    # Убедись, что используешь правильную версию модели. 
    # В твоем коде указана gemini-3.5-flash, которой пока не существует. 
    # Обычно используется gemini-1.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    # 1. Задаем системный промпт ментора
    mentor_prompt = (
        "Ты — элитный консультант по поступлению в топовые зарубежные университеты (включая Bocconi). "
        "Твоя задача — анализировать профиль абитуриента жестко, честно и экспертно. "
        "Твой стиль: дерзкий, уверенный, без капли воды. Говори с позиции сурового опыта. "
        "ЗАПРЕЩЕНО использовать ИИ-штампы ('Важно отметить', 'В заключение', 'Надеюсь, это поможет'). "
        "Используй сленг (транзитный год, GPA). Разделяй текст на короткие абзацы и используй Markdown: "
        "**жирный шрифт** для акцентов на метриках."
    )

    # 2. Формируем правильный payload с системными инструкциями
    payload = {
        "systemInstruction": {
            "parts": [{"text": mentor_prompt}]
        },
        "contents": [
            {"parts": [{"text": req.prompt}]}
        ]
    }
    
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

