from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

app = FastAPI()

# In-memory databases (for demo purposes)
users_db = {}
investments_db = {}

# Developer contact for alerts
DEVELOPER_PHONE = "0737734533"

class User(BaseModel):
    username: str
    password: str
    is_approved: bool = False
    failed_attempts: int = 0
    is_locked: bool = False

class Investment(BaseModel):
    username: str
    amount: float
    receipt_number: str
    approved: bool = False
    invested_on: datetime = datetime.now()
    last_paid: Optional[datetime] = None

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    if username in users_db:
        raise HTTPException(status_code=400, detail="User already exists.")
    users_db[username] = User(username=username, password=password)
    print(f"📲 ALERT: New user registered - {username}, Notify {DEVELOPER_PHONE}")
    return {"message": "Registration successful. Await admin approval."}

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = users_db.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.is_locked:
        raise HTTPException(status_code=403, detail="Account is locked.")
    if password != user.password:
        user.failed_attempts += 1
        if user.failed_attempts >= 3:
            user.is_locked = True
        raise HTTPException(status_code=401, detail="Incorrect password.")
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Account pending approval.")
    user.failed_attempts = 0
    return {"message": "Login successful."}

@app.post("/invest")
def invest(username: str = Form(...), amount: float = Form(...), receipt: str = Form(...)):
    if username not in users_db or not users_db[username].is_approved:
        raise HTTPException(status_code=403, detail="Unauthorized or unapproved user.")
    if amount < 500 or amount > 300000:
        raise HTTPException(status_code=400, detail="Investment must be between KSh 500 and 300,000.")
    investment = Investment(username=username, amount=amount, receipt_number=receipt)
    investments_db[username] = investment
    print(f"📲 ALERT: New investment by {username}, receipt {receipt}, Notify {DEVELOPER_PHONE}")
    return {"message": "Investment submitted. Await admin approval."}

@app.post("/approve_user")
def approve_user(username: str):
    user = users_db.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_approved = True
    return {"message": f"User {username} approved."}

@app.post("/approve_investment")
def approve_investment(username: str):
    investment = investments_db.get(username)
    if not investment:
        raise HTTPException(status_code=404, detail="No investment found.")
    investment.approved = True
    investment.last_paid = datetime.now()
    return {"message": f"Investment for {username} approved."}

@app.get("/earnings/{username}")
def calculate_earnings(username: str):
    investment = investments_db.get(username)
    if not investment or not investment.approved:
        raise HTTPException(status_code=404, detail="Approved investment not found.")
    now = datetime.now()
    days_passed = (now - investment.last_paid).days if investment.last_paid else 0
    daily_interest = 0.10
    sunday_bonus = 0.05 if now.weekday() == 6 else 0.0
    total = investment.amount * (daily_interest + sunday_bonus) * days_passed
    return {"earnings": round(total, 2), "days": days_passed}

@app.post("/withdraw")
def withdraw(username: str = Form(...)):
    today = datetime.now().weekday()
    if today != 0:
        raise HTTPException(status_code=403, detail="Withdrawals only allowed on Mondays.")
    investment = investments_db.get(username)
    if not investment or not investment.approved:
        raise HTTPException(status_code=404, detail="No approved investment.")
    total = investment.amount * 0.10  # Example: one day interest
    withdrawal_amount = total * 0.75  # 25% deduction
    print(f"📲 ALERT: Withdrawal by {username}, Notify {DEVELOPER_PHONE}")
    return {"message": f"Withdrawal request received. Amount after deduction: KSh {withdrawal_amount:.2f}"}
