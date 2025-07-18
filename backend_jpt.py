from fastapi import FastAPI, Form, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Dict
import uuid

app = FastAPI()

users: Dict[str, dict] = {}
investments: Dict[str, dict] = {}

JOINING_FEE = 1000  # Set the standard joining fee here

# =========================
# Models
# =========================

class Investment(BaseModel):
    username: str
    amount: float

class Approval(BaseModel):
    username: str

class Login(BaseModel):
    username: str
    password: str

class WithdrawRequest(BaseModel):
    username: str
    amount: float

# =========================
# Routes
# =========================

@app.get("/")
def root():
    return {"message": "Welcome to Jipate Bonus"}

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    if username in users:
        raise HTTPException(status_code=400, detail="User already exists")

    today = datetime.now()
    joining_fee = JOINING_FEE

    if today.strftime("%A") == "Sunday":
        joining_fee *= 0.95  # 5% discount

    users[username] = {
        "password": password,
        "approved": False,
        "registered_at": today,
        "joining_fee_paid": joining_fee,
        "balance": 0,
        "invested": 0,
        "investment_date": None
    }
    return {"message": f"User registered successfully. Joining fee paid: {joining_fee}"}

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful"}

@app.post("/invest")
def invest(investment: Investment):
    user = users.get(investment.username)
    if not user or not user["approved"]:
        raise HTTPException(status_code=403, detail="User not approved or doesn't exist")
    
    if user["investment_date"] is None:
        user["investment_date"] = datetime.now()
    
    user["invested"] += investment.amount
    user["balance"] += investment.amount
    return {"message": f"Invested {investment.amount} successfully."}

@app.post("/admin/approve_user")
def approve_user(approval: Approval):
    user = users.get(approval.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["approved"] = True
    return {"message": f"User {approval.username} approved."}

@app.post("/admin/approve_investment")
def approve_investment(approval: Approval):
    user = users.get(approval.username)
    if not user or not user["investment_date"]:
        raise HTTPException(status_code=404, detail="No investment found")
    
    now = datetime.now()
    days = (now - user["investment_date"]).days
    if days > 0:
        earnings = user["invested"] * 0.10 * days  # 10% per day
        user["balance"] += earnings
        user["investment_date"] = now
        return {"message": f"{days} days of earnings applied. Total earned: {earnings}"}
    else:
        return {"message": "No earnings to apply yet."}

@app.get("/admin/view_users")
def view_users():
    return users

@app.post("/earnings/daily")
def apply_daily_earnings(approval: Approval):
    user = users.get(approval.username)
    if not user or not user["investment_date"]:
        raise HTTPException(status_code=404, detail="No investment found")

    now = datetime.now()
    days = (now - user["investment_date"]).days
    if days > 0:
        earnings = user["invested"] * 0.10 * days
        user["balance"] += earnings
        user["investment_date"] = now
        return {"message": f"{days} days of earnings applied. Total earned: {earnings}"}
    else:
        return {"message": "No earnings to apply yet."}

@app.post("/withdraw")
def withdraw(request: WithdrawRequest):
    user = users.get(request.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if request.amount > user["balance"]:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    user["balance"] -= request.amount
    return {"message": f"Withdrew {request.amount} successfully."}
