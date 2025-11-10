from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime
import requests

# --- Hardcoded Configuration ---
BOT_TOKEN = "8502823873:AAEQpMyKFuZ4lYdNn7rmaBACh2d8-dPEXI4"
CHAT_ID = "6642388335"

# Railway MongoDB URL
MONGO_URI = "mongodb://mongo:RUyOPVmxOKQMeTIOSNtdYVAjrYrZaVWP@mainline.proxy.rlwy.net:35306"

client = MongoClient(MONGO_URI)
db = client.analytics
visits = db.visits

app = FastAPI()

# --- CORS Setup ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or replace "*" with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Functions ---
def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=3)
    except Exception as e:
        print("Telegram error:", e)

def get_unique_count(page: str, user_agent: str):
    """Insert visit if unique today and return total unique count."""
    today = datetime.utcnow().date()
    exists = visits.find_one({
        "page": page,
        "userAgent": user_agent,
        "date": today.isoformat()
    })
    if not exists:
        visits.insert_one({
            "page": page,
            "userAgent": user_agent,
            "date": today.isoformat(),
            "timestamp": datetime.utcnow()
        })
    total = visits.count_documents({"page": page, "date": today.isoformat()})
    return total

# --- API Endpoint ---
@app.post("/visit")
async def record_visit(request: Request):
    data = await request.json()
    page = data.get("page", "unknown")
    user_agent = data.get("userAgent", "Unknown")

    total_unique = get_unique_count(page, user_agent)

    # Send Telegram message
    time_now = datetime.now().strftime("%I:%M:%S %p")
    date_now = datetime.now().strftime("%m/%d/%Y")
    message = f"""
Page visit: {page}
Device: {user_agent}
Time: {time_now}
Date: {date_now}
TOTAL VISITORS (UNIQUE): {total_unique}
"""
    send_telegram(message.strip())
    return {"status": "ok", "total_unique": total_unique}
