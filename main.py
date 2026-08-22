import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from google import genai

# Ładowanie zmiennych środowiskowych
load_dotenv()

app = FastAPI()

# Konfiguracja szablonów
templates = Jinja2Templates(directory="templates")

# Inicjalizacja klienta Gemini
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else genai.Client()

# Lista aktywnych i najszybszych modeli w kolejności priorytetu
MODELS = ["gemini-3.6-flash", "gemini-3.5-flash"]

def ask_gemini(prompt: str) -> str:
    """Funkcja odpytująca modele z automatycznym przełączaniem w razie awarii lub limitu"""
    last_error = None
    for model_name in MODELS:
        try:
            print(f"[MODEL] Próba wywołania: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                print(f"[MODEL] Sukces: {model_name}")
                return response.text
        except Exception as e:
            last_error = e
            print(f"[MODEL BŁĄD] Model {model_name} zgłosił błąd: {e}")
            continue
            
    return f"Przepraszam szefa, Stark ma chwilowe spięcie w zbroi i serwery nie odpowiadają. Spróbuj za chwilę!"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Główna strona aplikacji dla syna"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """Endpoint do rozmowy ze Starkiem"""
    data = await request.json()
    user_message = data.get("message", "")
    
    # Prompt nadający charakter Tony'ego Starka / Iron Mana edukującego Maksa
    prompt = (
        "Jesteś Tonym Starkiem (Iron Manem) w wersji inteligentnego AI tutora pomagającego chłopcu o imieniu Maks. "
        "Odpowiadaj po polsku, wtrącaj czasem lekkie żarty lub klimatyczne teksty w stylu Marvela, ale tłumacz zagadnienia "
        "szkolne jasno, cierpliwie i wprost. "
        f"Wiadomość od Maksa: {user_message}"
    )
    
    reply = ask_gemini(prompt)
    return JSONResponse({"reply": reply})
