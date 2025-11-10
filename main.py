import asyncio
import random
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime

# --- Hardcoded Configuration ---
BOT_TOKEN = "8502823873:AAEQpMyKFuZ4lYdNn7rmaBACh2d8-dPEXI4"
CHAT_ID = "6642388335"
SELF_URL = "https://your-render-url.onrender.com/visit"  # Replace with your Render URL

# Railway MongoDB URL
MONGO_URI = "mongodb://mongo:RUyOPVmxOKQMeTIOSNtdYVAjrYrZaVWP@mainline.proxy.rlwy.net:35306"

client = MongoClient(MONGO_URI)
db = client.analytics
visits = db.visits

app = FastAPI()

# --- CORS Setup ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    return visits.count_documents({"page": page, "date": today.isoformat()})

# --- API Endpoint ---
@app.post("/visit")
async def record_visit(request: Request):
    data = await request.json()
    page = data.get("page", "unknown")
    user_agent = data.get("userAgent", "Unknown")

    total_unique = get_unique_count(page, user_agent)

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

# --- Background Task to Keep Service Alive ---
async def self_ping():
    await asyncio.sleep(10)  # wait a bit after startup
    while True:
        try:
            fake_page = f"keep_alive_{random.randint(1,1000)}"
            requests.post(SELF_URL, json={"page": fake_page, "userAgent": "ping_task"})
            print(f"Sent keep-alive ping: {fake_page}")
        except Exception as e:
            print("Keep-alive ping failed:", e)
        await asyncio.sleep(random.randint(240, 360))  # wait 4-6 minutes

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(self_ping())
