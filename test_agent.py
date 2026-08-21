import os
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError

API_KEY = "AQ.Ab8RN6LKjPvkxvW-tZ12nUQBOV5eUdWCN4e_NbWKWzJ24N8mYw"

client = genai.Client(api_key=API_KEY)

system_instruction = """
Jesteś cierpliwym, życzliwym i wyrozumiałym nauczycielem i korepetytorem.
Twój uczeń jest w klasie 5 szkoły podstawowej.
Dostosowuj język, przykłady i poziom trudności do wieku 11 lat.
Gdy uczeń zadaje pytanie dotyczące zadań, NIE podawaj od razu gotowej odpowiedzi.
Zamiast tego wytłumacz koncepcję krok po kroku i zadaj pytanie pomocnicze,
zmuszając go do samodzielnego myślenia (metoda sokratejska).
"""

chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.7,
    ),
)

print("--- AGENT NAUCZYCIEL GOTOWY DO ROZMOWY ---")
print("Wpisz 'wyjdz', 'wyjdź' lub 'exit', aby zakończyć.\n")

slowa_wyjscia = ["wyjdz", "wyjdź", "exit", "quit", "q"]

while True:
    try:
        user_input = input("Uczeń: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nNauczyciel: Do zobaczenia na następnej lekcji!")
        break

    if user_input.lower() in slowa_wyjscia:
        print("Nauczyciel: Do zobaczenia na następnej lekcji!")
        break

    if not user_input:
        continue

    # Pętla obsługująca chwilowy brak dostępności serwera (błąd 503)
    sukces = False
    proby = 0
    while not sukces and proby < 3:
        try:
            response = chat.send_message(user_input)
            print(f"\nNauczyciel:\n{response.text}\n")
            sukces = True
        except APIError as e:
            proby += 1
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print(f"\n[Serwer AI jest chwilowo zajęty. Ponowna próba ({proby}/3)...]")
                time.sleep(2)
            else:
                print(f"\nWystąpił błąd API: {e}")
                break
        except Exception as e:
            print(f"\nWystąpił nieoczekiwany błąd: {e}")
            break
