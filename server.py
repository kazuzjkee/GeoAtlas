from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import random
import time
import os
import smtplib
from email.message import EmailMessage
import json

app = FastAPI(title="Геоатлас Ростовской области — Портал ЮФУ")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

verification_storage = {}
RESULTS_FILE = "quiz_results.json"

class AuthRequest(BaseModel):
    email: str
    full_name: str
    group_num: str

class VerifyRequest(BaseModel):
    email: str
    code: str

class ResultSubmit(BaseModel):
    email: str
    name: str
    group: str
    quiz_type: str
    score: int
    max_score: int
    accuracy: int
    time_spent: str

def load_results():
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_result_to_file(result_data):
    results = load_results()
    results.append(result_data)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def send_email_smtp(to_email: str, code: str):
    smtp_server = "smtp.yandex.ru"
    smtp_port = 465
    sender_email = "egorlitwinoff@yandex.ru"
    app_password = "eyqmygxejtjceaee"

    msg = EmailMessage()
    msg.set_content(
        f"Здравствуйте, студенческий профиль ЮФУ!\n\n"
        f"Ваш код подтверждения для входа в картографический атлас Ростовской области: {code}\n\n"
        f"Код действителен в течение 10 минут."
    )
    msg["Subject"] = "Код авторизации | Атлас Ростовской области"
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        print(f"✅ Письмо успешно отправлено на почту: {to_email}")
    except Exception as e:
        print(f"⚠️ Ошибка отправки SMTP (DEV дубль в консоль): {e}")
        print(f"🔑 [DEV ДУБЛЬ] Код для {to_email}: {code}")


@app.post("/api/auth/send-code")
def send_code(req: AuthRequest):
    email = req.email.strip().lower()
    if not (email.endswith("@sfedu.ru") or email.endswith(".sfedu.ru")):
        raise HTTPException(status_code=400, detail="Разрешена авторизация только по корпоративной почте ЮФУ (@sfedu.ru)")
    
    code = f"{random.randint(100000, 999999)}"
    verification_storage[email] = {
        "code": code,
        "expires_at": time.time() + 600,
        "name": req.full_name.strip(),
        "group": req.group_num.strip()
    }
    print(f"\n🔑 [ЮФУ АВТОРИЗАЦИЯ] Код для {email}: {code}\n")
    send_email_smtp(email, code)
    return {"status": "ok", "message": "Код подтверждения отправлен"}


@app.post("/api/auth/verify-code")
def verify_code(req: VerifyRequest):
    email = req.email.strip().lower()
    record = verification_storage.get(email)
    if not record or time.time() > record["expires_at"] or record["code"] != req.code.strip():
        raise HTTPException(status_code=400, detail="Неверный или просроченный код")
    
    user_data = {"email": email, "name": record["name"], "group": record["group"]}
    del verification_storage[email]
    return {"status": "ok", "user": user_data}


@app.post("/api/results/save")
def save_quiz_result(res: ResultSubmit):
    data = {
        "date": time.strftime("%d.%m.%Y %H:%M"),
        "email": res.email,
        "name": res.name,
        "group": res.group,
        "quiz_type": res.quiz_type,
        "score": res.score,
        "max_score": res.max_score,
        "accuracy": res.accuracy,
        "time_spent": res.time_spent
    }
    save_result_to_file(data)
    return {"status": "ok"}


@app.get("/api/results/leaderboard")
def get_leaderboard():
    results = load_results()
    sorted_res = sorted(results, key=lambda x: (x["accuracy"], x["score"]), reverse=True)
    return sorted_res[:20]


@app.get("/")
def get_index():
    return FileResponse("rostov_quiz_map.html")


if __name__ == "__main__":
    import uvicorn
    print("\nСервер запущен! Перейдите в браузере по адресу: http://127.0.0.1:8000\n")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)