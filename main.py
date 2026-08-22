import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from google import genai

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Bezpieczna inicjalizacja klienta
api_key = os.getenv("GEMINI_API_KEY")
try:
    client = genai.Client(api_key=api_key) if api_key else genai.Client()
except Exception as e:
    print(f"Błąd inicjalizacji klienta: {e}")
    client = None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message", "")
        
        prompt = (
            "Jesteś Tonym Starkiem (Iron Manem) w wersji inteligentnego AI tutora pomagającego chłopcu o imieniu Maks. "
            "Odpowiadaj po polsku, wtrącaj czasem lekkie żarty lub klimatyczne teksty w stylu Marvela, ale tłumacz zagadnienia "
            "szkolne jasno, cierpliwie i wprost. "
            f"Wiadomość od Maksa: {user_message}"
        )
        
        if not client:
            return JSONResponse({"reply": "Systemy Starka są offline - brak klucza API."})

        # Próba wywołania stabilnego modelu
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
        )
        reply = response.text if response and response.text else "Stark nie uzyskał odpowiedzi."
        return JSONResponse({"reply": reply})
        
    except Exception as e:
        print(f"Błąd w chat_endpoint: {e}")
        return JSONResponse({"reply": "Przepraszam szefa, Stark ma chwilowe spięcie w zbroi!"})
