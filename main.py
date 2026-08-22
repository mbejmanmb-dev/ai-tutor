import os
import json
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from google import genai
from google.genai import types

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StarkLab")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

DB_FILE = "chat_history.json"
DEFAULT_USER = "Maks"

LISTA_MODELI_CHAT = [
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite"
]

LISTA_MODELI_QUIZ = [
    "gemini-3.5-flash",
    "gemini-2.5-pro",
    "gemini-3.6-flash",
    "gemini-2.5-flash"
]

PROMPT_SYSTEMOWY = """Jesteś cierpliwym, niezwykle inteligentnym i przyjaznym Korepetytorem AI, stylizowanym na Tony'ego Starka / Iron Mana dla ucznia szkoły podstawowej (Maks, klasa 6). 
Pomagasz w nauce w sposób jasny, nowoczesny i pełen humoru. Pamiętaj całą historię rozmowy i nawiązuj do wcześniej omówionych tematów.

BEZWZGLĘDNE ZASADY FORMATOWANIA TEKSTU I BEZPIECZEŃSTWA FORMATU:
1. ZAKAZ LATEX ORAZ ZNAKÓW DOLARA: Nigdy nie pisz symboli '$' ani wyrażeń typu $3 \\times 7$. Pisząc działania matematyczne, używaj zwykłych liter i znaków, np.: 3 x 7 = 21, 9 x 4 = 36.
2. ZAKAZ NAGŁÓWKÓW MARKDOWN: Nie używaj '###', '##' ani '#'. Do wyróżniania sekcji stosuj wyłącznie pogrubienia tekstowe, np. **ETAP 1: Super-triki Starka**.
3. WIZUALIZACJA I TABELE: Jeśli tworzysz tabelę lub wizualizację, PISZ JEJ KOD WYŁĄCZNIE W CZYSTYM HTML (używając tagów <table border="1">, <tr>, <th>, <td>). Nie używaj tabel w formacie Markdown z pionowymi kreskami '|'.

Struktura odpowiedzi:
- ETAP 1: Podaj jasną, zwięzłą definicję lub odpowiedź na pytanie ucznia.
- WIZUALIZACJA: Jeśli temat tego wymaga (np. tabliczka mnożenia, wzory, schematy), umieść estetyczną tabelę HTML.
- ETAP 2: Zadaj 1 krótkie pytanie sprawdzające wiedzę ucznia."""

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[BŁĄD BAZY] Nie udało się odczytać historii: {e}")
    return {DEFAULT_USER: []}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[BŁĄD BAZY] Zapis historii nie powiódł się: {e}")

db_data = load_db()

class ChatRequest(BaseModel):
    message: str

class QuizRequest(BaseModel):
    subject: str
    topic: str
    num_questions: int = 3

def generate_with_fallback(contents, config=None, is_quiz=False):
    model_list = LISTA_MODELI_QUIZ if is_quiz else LISTA_MODELI_CHAT
    last_exception = None

    for model_name in model_list:
        try:
            logger.info(f"[MODEL] Wywołanie: {model_name}")
            kwargs = {"model": model_name, "contents": contents}
            if config:
                kwargs["config"] = config

            response = client.models.generate_content(**kwargs)
            logger.info(f"[MODEL] Sukces: {model_name}")
            return response.text
        except Exception as e:
            logger.error(f"[MODEL BŁĄD] Model {model_name} zgłosił błąd: {str(e)}")
            last_exception = e
            continue

    raise last_exception or Exception("Wszystkie modele zawiodły.")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/history")
async def get_history():
    history = db_data.get(DEFAULT_USER, [])
    return JSONResponse(content=history)

@app.delete("/api/history")
async def clear_history():
    db_data[DEFAULT_USER] = []
    save_db(db_data)
    logger.info("[HISTORIA] Historia została wyczyszczona.")
    return {"status": "success"}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not GEMINI_API_KEY or not client:
        logger.error("[SYSTEM] Brak klucza GEMINI_API_KEY w pliku .env")
        return JSONResponse(content={"reply": "Brak konfiguracji klucza API po stronie serwera."})

    history = db_data.get(DEFAULT_USER, [])

    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
    
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=req.message)]))

    config = types.GenerateContentConfig(
        system_instruction=PROMPT_SYSTEMOWY,
        temperature=0.7,
    )

    try:
        reply_text = generate_with_fallback(contents, config=config, is_quiz=False)

        history.append({"role": "user", "content": req.message})
        history.append({"role": "bot", "content": reply_text})
        db_data[DEFAULT_USER] = history
        save_db(db_data)

        return JSONResponse(content={"reply": reply_text})
    except Exception as e:
        logger.error(f"[BŁĄD CHAT] Awarie po stronie API: {str(e)}")
        return JSONResponse(content={"reply": "Przepraszam, wystąpił chwilowy problem techniczny z połączeniem."})

@app.post("/api/quiz")
async def generate_quiz(req: QuizRequest):
    if not GEMINI_API_KEY or not client:
        logger.error("[SYSTEM] Brak klucza GEMINI_API_KEY")
        return JSONResponse(content={"quiz": "Brak klucza API."})

    prompt = f"""Wygeneruj krótki sprawdzian/quiz dla ucznia 6 klasy (Maks) z przedmiotu: {req.subject}.
Temat: {req.topic}.
Liczba pytań: {req.num_questions}.

Format wyjścia:
Napisz pytania jedno po drugim z 3 opcjami odpowiedzi (A, B, C).
Na samym końcu podaj klucz poprawnych odpowiedzi:
---
Klucz odpowiedzi:
1. ...
2. ...
"""
    try:
        quiz_text = generate_with_fallback(prompt, is_quiz=True)
        return {"quiz": quiz_text}
    except Exception as e:
        logger.error(f"[BŁĄD QUIZ]: {str(e)}")
        return JSONResponse(content={"quiz": "Nie udało się wygenerować quizu."})
