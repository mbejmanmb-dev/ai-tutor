import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
from google import genai

load_dotenv()
app = FastAPI()

api_key = os.getenv("GEMINI_API_KEY")
try:
    client = genai.Client(api_key=api_key) if api_key else genai.Client()
except Exception as e:
    print(f"Błąd inicjalizacji klienta: {e}")
    client = None

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Bezpośrednie wczytanie pliku index.html - zero błędów Jinja2/Starlette
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Błąd ładowania szablonu: {e}</h1>", status_code=500)

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

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
        )
        reply = response.text if response and response.text else "Stark nie uzyskał odpowiedzi."
        return JSONResponse({"reply": reply})
        
    except Exception as e:
        print(f"Błąd w chat_endpoint: {e}")
        return JSONResponse({"reply": "Przepraszam szefa, Stark ma chwilowe spięcie w zbroi!"})
