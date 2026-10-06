import os
import json
from flask import Flask, request
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import requests

app = Flask(__name__)

# Config
TELEGRAM_TOKEN = "8617783972:AAGnxrjeGerMQIBHp6A_qlpAlIEwnSEXu_k"
SHEET_ID = "1IOWqwqKaSH-YO9xB_CS2BJuSa6W6zMKdgZqpN_moiLA"
SHEET_NAME = "Datos Brutos"

VALID_CATEGORIES = [
    "Alquiler/Vivienda", "Agua/gas/electricidad", "Televisión+Internet", "Teléfono",
    "Supermercado", "Comida laburo", "Restaurantes", "Transporte público", "Bicing",
    "Moto (YEGO)", "Uber", "Viajes", "Ropa", "Perfume", "Chiches/Objetos",
    "Gastos médicos", "Basket/Padel", "Gym", "Claude/Anthropic", "Amazon Prime",
    "Cursos", "Otros", "Regalos", "Seguros", "Tabaco", "Donaciones", "Inversiones"
]

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def send_telegram_keyboard(chat_id, text, options):
    keyboard = [[{"text": opt, "callback_data": opt}] for opt in options]
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {"inline_keyboard": keyboard}
    })

def save_to_sheets(date, descripcion, monto, categoria):
    try:
        credentials = Credentials.from_service_account_info(json.loads(os.getenv("GOOGLE_CREDS")))
        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        sheet.append_row([date, "", date, descripcion, -monto, categoria, "Telegram"])
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    data = request.json
    message = data.get("message")
    
    if not message:
        return "ok"
    
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    
    if text == "/start":
        send_telegram_message(chat_id, "Bienvenido! Formato: Descripción\nLuego te preguntaré categoría y monto.")
        return "ok"
    
    parts = [p.strip() for p in text.split(" - ")]
    
    if len(parts) == 1:
        # Primer step: descripción
        descripcion = text
        send_telegram_keyboard(chat_id, f"Descripción: {descripcion}\n\nElige categoría:", VALID_CATEGORIES)
        return "ok"
    
    # TODO: implementar flujo completo con callbacks
    
    send_telegram_message(chat_id, "❌ Formato: Descripción - Categoría - Monto")
    return "ok"

@app.route("/")
def index():
    return "Bot running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
