import os
import urllib.parse
import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional

# Load environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
PORT = int(os.getenv("PORT", 8080))

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# FastAPI setup
app = FastAPI(title="Nova Image Generator API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Prompt(BaseModel):
    prompt: str

class ImageData(BaseModel):
    prompt: Optional[str] = None
    url: str

@app.get("/")
def root():
    return {"status": "ok", "message": "Connected to Render Docker"}

@app.get("/db-test")
def db_test():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        time = cur.fetchone()
        conn.close()
        return {"db_status": "connected", "time": str(time[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB Test failed: {e}")

@app.post("/generate")
async def generate_image(data: Prompt):
    encoded_prompt = urllib.parse.quote_plus(data.prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    return {"url": image_url}

@app.post("/save")
async def save_image(data: ImageData):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS images (id SERIAL PRIMARY KEY, prompt TEXT, url TEXT)")
        cur.execute("INSERT INTO images (prompt, url) VALUES (%s, %s)", (data.prompt, data.url))
        conn.commit()
        conn.close()
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save error: {e}")

@app.get("/history")
async def get_history():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT prompt, url FROM images ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        images = [{"prompt": r[0], "url": r[1]} for r in rows]
        return {"images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History read error: {e}")
