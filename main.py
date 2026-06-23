from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

app = FastAPI(title="UniCalc API Pro", description="Мозг платформы: База + Премиум функции")

# --- НАСТРОЙКИ CORS (ПРОПУСК ДЛЯ ФРОНТЕНДА) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- 1. ЗАГРУЗКА БАЗЫ ДАННЫХ ---
try:
    with open('data.json', 'r', encoding='utf-8') as file:
        database = json.load(file)
except Exception as e:
    database = {"cities_and_vuz": {}}

# --- 2. СТРУКТУРЫ ДАННЫХ (Что мы ждем от пользователя) ---
class UserProfile(BaseModel):
    vuz_key: str
    major_key: str
    gpa: float
    ielts: float
    sat: int
    portfolio_val: float
    savings: float

class TransferRequest(BaseModel):
    local_uni_gpa: float
    completed_years: int
    target_country: str

class VisaRequest(BaseModel):
    target_country: str
    available_funds: float

class ROIData(BaseModel):
    total_education_cost: float
    expected_annual_salary: float


# --- 3. БАЗОВЫЕ ФУНКЦИИ (Бесплатный тариф) ---
@app.get("/api/universities")
def get_universities():
    return database

@app.post("/api/calculate")
def calculate_chances(profile: UserProfile):
    vuz = database["cities_and_vuz"].get(profile.vuz_key)
    if not vuz: raise HTTPException(status_code=404, detail="Университет не найден")
    major = vuz.get("majors", {}).get(profile.major_key)
    if not major: raise HTTPException(status_code=404, detail="Направление не найдено")

    p_gpa, p_ielts, p_sat = major.get('paid_gpa', 0), major.get('paid_ielts', 0), major.get('paid_sat', 0)
    g_gpa, g_ielts, g_sat = major.get('grant_gpa', 0), major.get('grant_ielts', 0), major.get('grant_sat', 0)
    
    status, chance, tuition = "", 0, vuz.get('tuition_annual', 0)
    
    if profile.gpa < p_gpa or profile.ielts < p_ielts or (p_sat > 0 and profile.sat < p_sat):
        status, chance = "ОТКАЗ", 0
    elif profile.gpa >= g_gpa and profile.ielts >= g_ielts and (g_sat == 0 or profile.sat >= g_sat):
        status, chance, tuition = "ГРАНТ", min(99, 70 + (profile.portfolio_val * vuz.get('weight_grant', 0.3) * 100)), 0 
    else:
        status, chance = "ПЛАТНОЕ", min(95, 80 + (profile.portfolio_val * vuz.get('weight_paid', 0.05) * 100))
        
    living = (vuz.get('rent_monthly', 0) + vuz.get('food_monthly', 0) + vuz.get('transport_monthly', 0)) * 12
    return {"status": status, "chance": round(chance, 1), "deficit": (living + tuition) - profile.savings}


# --- 4. ПРЕМИУМ ФУНКЦИИ (Pro Тариф) ---

@app.post("/api/premium/transfer")
def check_transfer(req: TransferRequest):
    """Проверяет возможность перевода из местного вуза (закрытие 12 лет)"""
    requires_12_years = ["Италия", "Германия", "Финляндия"]
    
    if req.target_country in requires_12_years and req.completed_years < 1:
        return {"status": "ОТКАЗ", "reason": f"Для страны '{req.target_country}' требуется минимум 1 год в местном вузе."}
    
    if req.local_uni_gpa < 3.5:
        return {"status": "ОТКАЗ", "reason": "GPA в местном вузе слишком низкий для конкурентного перевода."}
        
    return {"status": "ОДОБРЕНО", "reason": "Вы соответствуете академическим требованиям для перевода."}

@app.post("/api/premium/visa")
def check_visa(req: VisaRequest):
    """Считает, хватит ли денег на счету для получения визы"""
    # Средние требования консульств в евро/долларах в год
    visa_requirements = {"Италия": 6000, "США": 25000, "Канада": 15000, "Финляндия": 8000}
    needed = visa_requirements.get(req.target_country, 10000) # По умолчанию 10000
    
    if req.available_funds >= needed:
        return {"visa_status": "🟢 БЕЗОПАСНО", "message": f"Средств достаточно. Требуется: {needed}, У вас: {req.available_funds}"}
    return {"visa_status": "🔴 РИСК ОТКАЗА", "message": f"Не хватает {needed - req.available_funds} для выписки в консульство."}

@app.post("/api/premium/roi")
def calculate_roi(req: ROIData):
    """Считает срок окупаемости диплома (через сколько лет отобьются вложения)"""
    if req.expected_annual_salary <= 0:
        return {"error": "Зарплата должна быть больше нуля"}
    
    # Допустим, выпускник может откладывать 30% зарплаты на покрытие долга за учебу
    savings_per_year = req.expected_annual_salary * 0.30 
    years_to_payoff = req.total_education_cost / savings_per_year
    
    return {
        "roi_years": round(years_to_payoff, 1),
        "message": f"С учетом стартовой зарплаты {req.expected_annual_salary}, диплом окупится за {round(years_to_payoff, 1)} лет."
    }