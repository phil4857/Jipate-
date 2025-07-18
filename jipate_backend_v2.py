from fastapi import FastAPI, Form, UploadFile, File
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class User(BaseModel):
    username: str
    password: str

@app.post("/register/")
async def register(user: User):
    return {"message": f"User {user.username} registered successfully"}

@app.post("/invest/")
async def invest(amount: float = Form(...), receipt: str = Form(...)):
    if amount < 500 or amount > 300000:
        return {"error": "Amount must be between KSh 500 and 300,000"}
    return {
        "message": "Investment received",
        "amount": amount,
        "receipt": receipt,
        "status": "Pending approval"
    }

@app.get("/")
async def root():
    return {"message": "Welcome to Jipate Bonus Platform"}
