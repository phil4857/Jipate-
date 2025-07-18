
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Dict, Optional
import uuid

app = FastAPI()

# In-memory databases
users: Dict[str, dict] = {}
investments: Dict[str, dict] = {}

# Constants
JOINING_FEE = 1000
DAILY_EARNING_PERCENT = 0.10
SUNDAY_DISCOUNT = 0.05
REFERRAL_REWARD = 200

def is_sunday():
    return datetime.now().weekday() == 6

@app.get("/")
def root():
    return {"message": "Welcome to Jipate Bonus"}

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...), referrer_code: Optional[str] = Form(None)):
    if username in users:
        raise HTTPException(status_code=400, detail="Username already exists")

    joining_fee = JOINING_FEE
    if is_sunday():
        joining_fee -= JOINING_FEE * SUNDAY_DISCOUNT

    referral_id = str(uuid.uuid4())[:6]

    users[username] = {
        "username": username,
        "password": password,
        "approved": False,
        "joined_on": str(datetime.now()),
        "referral_id": referral_id,
        "referrer_code": referrer_code,
        "referral_earned": 0,
        "invested": False,
        "balance": 0
    }
    return {"message": "User registered successfully", "joining_fee": joining_fee, "referral_id": referral_id}

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful"}

@app.post("/invest")
def invest(username: str = Form(...), amount: float = Form(...)):
    user = users.get(username)
    if not user or not user["approved"]:
        raise HTTPException(status_code=403, detail="User not approved or doesn't exist")

    if username in investments:
        raise HTTPException(status_code=400, detail="User already has an investment")

    investments[username] = {
        "amount": amount,
        "last_earning_date": datetime.now()
    }
    user["invested"] = True

    # Reward referrer if applicable
    ref_code = user.get("referrer_code")
    if ref_code:
        for u in users.values():
            if u["referral_id"] == ref_code:
                u["referral_earned"] += REFERRAL_REWARD
                u["balance"] += REFERRAL_REWARD
                break

    return {"message": "Investment successful", "amount": amount}

@app.post("/admin/approve_user")
def approve_user(username: str = Form(...)):
    user = users.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["approved"] = True
    return {"message": f"User {username} approved."}

@app.post("/admin/approve_investment")
def approve_investment(username: str = Form(...)):
    if username not in users or username not in investments:
        raise HTTPException(status_code=404, detail="User or investment not found")
    # Assume "approved" means investment is ready to earn
    return {"message": f"Investment for {username} approved."}

@app.post("/earnings/daily")
def apply_daily_earnings():
    applied_users = []
    for username, data in investments.items():
        last_date = data["last_earning_date"]
        if datetime.now() - last_date >= timedelta(days=1):
            earnings = data["amount"] * DAILY_EARNING_PERCENT
            users[username]["balance"] += earnings
            data["last_earning_date"] = datetime.now()
            applied_users.append({"username": username, "earned": earnings})
    return {"message": "Daily earnings applied", "details": applied_users}

@app.post("/withdraw")
def withdraw(username: str = Form(...), amount: float = Form(...)):
    user = users.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if amount > user["balance"]:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    user["balance"] -= amount
    return {"message": f"Withdrawal of {amount} successful", "remaining_balance": user["balance"]}

@app.get("/admin/view_users")
def view_users():
    return {"users": list(users.values())}
