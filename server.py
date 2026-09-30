from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import random
import time
import os
import smtplib
from email.message import EmailMessage
import json
import secrets
import csv
import io

# Автоматически генерируем карту при старте сервера, если её нет
if not os.path.exists("rostov_quiz_map.html"):
    print("Карта rostov_quiz_map.html не найдена, запускаем генерацию через main.py...")
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", "main — копия_2.py")
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)
    main_module.main()

app = FastAPI(title="Геоатлас Ростовской области — Портал ЮФУ")
security = HTTPBasic()

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
        except Exception:
            return []
    return []

def save_result_to_file(result_data):
    results = load_results()
    results.append(result_data)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def check_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, "sfedu_admin")
    correct_pass = secrets.compare_digest(credentials.password, "geodean2026")
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль преподавателя",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

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
    print(f"\n🔑 [ЮФУ АВТОРИЗАЦИЯ] Сгенерирован код для {email}: {code}\n")
    return {"status": "ok", "message": "Код подтверждения отправлен", "dev_code": code}

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
    sorted_res = sorted(results, key=lambda x: (x.get("accuracy", 0), x.get("score", 0)), reverse=True)
    return sorted_res[:25]

# ================= МАКСИМАЛЬНО ФУНКЦИОНАЛЬНАЯ ПАНЕЛЬ ПРЕПОДАВАТЕЛЯ =================
@app.get("/admin", response_class=HTMLResponse)
def admin_panel(username: str = Depends(check_admin)):
    results = load_results()
    total_tests = len(results)
    avg_accuracy = round(sum(r.get("accuracy", 0) for r in results) / total_tests, 1) if total_tests else 0
    
    # Сводка по группам
    groups_stat = {}
    for r in results:
        grp = r.get("group", "Не указана")
        groups_stat.setdefault(grp, []).append(r.get("accuracy", 0))
    
    groups_rows = ""
    for grp, accs in groups_stat.items():
        g_avg = round(sum(accs) / len(accs), 1)
        groups_rows += f"<tr><td><b>{grp}</b></td><td>{len(accs)}</td><td><div style='background:#E2E8F0; border-radius:4px; overflow:hidden;'><div style='background:#10B981; width:{g_avg}%; height:8px;'></div></div> {g_avg}%</td></tr>"

    rows = ""
    for r in reversed(results):
        rows += f"""
        <tr>
            <td>{r.get('date')}</td>
            <td><b>{r.get('name')}</b><br><small style="color:#64748B;">{r.get('email')}</small></td>
            <td>{r.get('group')}</td>
            <td><span class="type-tag">{r.get('quiz_type')}</span></td>
            <td><b>{r.get('score')}/{r.get('max_score')}</b></td>
            <td><span class="badge">{r.get('accuracy')}%</span></td>
            <td>{r.get('time_spent')}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Панель преподавателя | Геоатлас ЮФУ</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #F8FAFC; margin: 0; padding: 24px; color: #1E293B; }}
            .container {{ max-width: 1100px; margin: 0 auto; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #E2E8F0; padding-bottom: 16px; margin-bottom: 24px; }}
            .card-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }}
            .stat-card {{ background: white; padding: 18px; border-radius: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #E2E8F0; }}
            .stat-val {{ font-size: 28px; font-weight: 800; color: #0284C7; margin-top: 4px; }}
            table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #E2E8F0; margin-bottom: 24px; }}
            th, td {{ padding: 11px 14px; text-align: left; font-size: 13px; border-bottom: 1px solid #F1F5F9; }}
            th {{ background: #F8FAFC; color: #64748B; font-weight: 700; }}
            .badge {{ background: #DCFCE7; color: #166534; font-weight: 700; padding: 3px 8px; border-radius: 6px; }}
            .type-tag {{ background: #E0F2FE; color: #0369A1; padding: 3px 8px; border-radius: 6px; font-size: 11.5px; font-weight: 600; }}
            .btn {{ text-decoration: none; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 700; display: inline-block; cursor: pointer; border: none; }}
            .btn-primary {{ background: #10B981; color: white; }}
            .btn-primary:hover {{ background: #059669; }}
            .btn-back {{ background: #0284C7; color: white; }}
            .actions-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h2 style="margin: 0;">🎓 Аналитическая панель преподавателя</h2>
                    <p style="margin: 4px 0 0 0; color: #64748B; font-size: 13px;">Институт наук о Земле ЮФУ — Мониторинг успеваемости студентов</p>
                </div>
                <a href="/" class="btn btn-back">← На карту атласа</a>
            </div>

            <div class="card-grid">
                <div class="stat-card">
                    <div style="font-size: 12px; color: #64748B; font-weight: 600;">Всего сданных тестов</div>
                    <div class="stat-val">{total_tests}</div>
                </div>
                <div class="stat-card">
                    <div style="font-size: 12px; color: #64748B; font-weight: 600;">Средняя результативность</div>
                    <div class="stat-val">{avg_accuracy}%</div>
                </div>
                <div class="stat-card">
                    <div style="font-size: 12px; color: #64748B; font-weight: 600;">Активных групп</div>
                    <div class="stat-val">{len(groups_stat)}</div>
                </div>
            </div>

            <h3 style="font-size: 16px; margin-bottom: 10px;">Сводка по учебным группам</h3>
            <table>
                <tr><th>Академическая группа</th><th>Количество попыток</th><th>Средний показатель успеваемости</th></tr>
                {groups_rows if groups_rows else "<tr><td colspan='3' style='text-align: center; color: #94A3B8;'>Пока нет данных тестирования</td></tr>"}
            </table>

            <div class="actions-bar">
                <h3 style="font-size: 16px; margin: 0;">Журнал прохождений студентов</h3>
                <a href="/admin/export-csv" class="btn btn-primary">📥 Экспорт ведомости в CSV</a>
            </div>
            <table>
                <tr><th>Дата и время</th><th>Студент</th><th>Группа</th><th>Вид викторины</th><th>Баллы</th><th>% успеха</th><th>Время</th></tr>
                {rows if rows else "<tr><td colspan='7' style='text-align: center; color: #94A3B8;'>Журнал пуст</td></tr>"}
            </table>
        </div>
    </body>
    </html>
    """

@app.get("/admin/export-csv", response_class=PlainTextResponse)
def export_csv(username: str = Depends(check_admin)):
    results = load_results()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Дата', 'ФИО студента', 'Email', 'Группа', 'Тип теста', 'Баллы', 'Макс баллов', 'Успешность (%)', 'Затраченное время'])
    
    for r in results:
        writer.writerow([
            r.get('date'), r.get('name'), r.get('email'), r.get('group'),
            r.get('quiz_type'), r.get('score'), r.get('max_score'),
            r.get('accuracy'), r.get('time_spent')
        ])
    
    response = PlainTextResponse(output.getvalue(), media_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = "attachment; filename=vedomost_ufuv_geos.csv"
    return response

@app.get("/")
def get_index():
    return FileResponse("rostov_quiz_map.html")

if __name__ == "__main__":
    import uvicorn
    print("\nСервер запущен! Перейдите в браузере:")
    print("  - Картографический атлас: http://127.0.0.1:8000")
    print("  - Панель преподавателя:   http://127.0.0.1:8000/admin (Логин: sfedu_admin / Пароль: geodean2026)\n")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)