from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

# Simulated user storage
users = {}

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    if username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    users[username] = {
        "password": password,
        "created_at": datetime.utcnow()
    }
    return {"message": "User registered successfully"}

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": f"Welcome {username}"}

@app.get("/")
def root():
    return {"message": "Jipate Bonus API is live!"}
