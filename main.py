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

user_state = {}

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def send_telegram_buttons(chat_id, text, options):
    keyboard = [[{"text": opt, "callback_data": f"cat_{opt}"}] for opt in options]
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {"inline_keyboard": keyboard}
    })

def save_to_sheets(date, descripcion, monto, categoria):
    try:
        creds_json = os.getenv("GOOGLE_CREDS")
        if not creds_json:
            return False
        credentials = Credentials.from_service_account_info(json.loads(creds_json))
        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        sheet.append_row([date, "", date, descripcion, -monto, categoria, "Telegram"])
        return True
    except Exception as e:
        print(f"Error saving: {e}")
        return False

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    data = request.json
    
    # Handle text messages
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()
        
        if text == "/start":
            send_telegram_message(chat_id, "¡Bienvenido! 👋\n\nVoy a ayudarte a registrar gastos.\n\n¿Cuál es la descripción del gasto?")
            user_state[chat_id] = {"step": "descripcion"}
            return "ok"
        
        # Step 1: Get description
        if chat_id in user_state and user_state[chat_id]["step"] == "descripcion":
            user_state[chat_id]["descripcion"] = text
            user_state[chat_id]["step"] = "categoria"
            send_telegram_buttons(chat_id, f"✅ Descripción: {text}\n\n¿Qué categoría?", VALID_CATEGORIES)
            return "ok"
        
        # Step 3: Get amount (if coming from text, not callback)
        if chat_id in user_state and user_state[chat_id]["step"] == "monto":
            try:
                monto = float(text)
                if monto <= 0:
                    raise ValueError
                descripcion = user_state[chat_id]["descripcion"]
                categoria = user_state[chat_id]["categoria"]
                date = datetime.now().strftime("%m/%d/%Y")
                
                if save_to_sheets(date,
